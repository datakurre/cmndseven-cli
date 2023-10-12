import base64
import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

import chameleon  # type: ignore
import click
import generic_camunda_client  # type: ignore
from click import Context, Argument, Option, Parameter, ParamType
from generic_camunda_client.rest import ApiException  # type: ignore

ASSETS = [
    Path(__file__).parent / "assets" / "index.js",
    Path(__file__).parent / "assets" / "bpmn-viewer.production.min.js",
    Path(__file__).parent / "assets" / "puppeteer.production.min.js",
]

NODEJS_EXECUTABLE_PATH = str(shutil.which("node"))
PUPPETEER_EXECUTABLE_PATH = str(shutil.which("chrome") or shutil.which("chromium"))


@dataclass
class GlobalOptions:
    """Global API client options."""

    url: str
    authorization: str = ""


class CamundaApiClient(generic_camunda_client.ApiClient):
    """Patched generated client to support authentication."""

    def __init__(self, options: GlobalOptions, *args, **kwargs):
        """Initialize client with global CLI options."""

        configuration = generic_camunda_client.Configuration(host=options.url)
        super().__init__(configuration, *args, **kwargs)
        if options.authorization:
            self.default_headers["Authorization"] = options.authorization


class PlainTextApiClient(CamundaApiClient):
    def select_header_accept(self, accepts: List[str]):
        return "text/plain"


def data_uri(mimetype: str, data: bytes):
    return "data:{};base64,{}".format(mimetype, base64.b64encode(data).decode("utf-8"))


@click.group(help="Camunda Platform 7 CLI")
@click.option(
    "--url",
    envvar="CAMUNDA_URL",
    default="http://localhost:8080/engine-rest",
    help="Set Camunda REST API base URL (env: CAMUNDA_URL).",
)
@click.option(
    "--authorization",
    envvar="CAMUNDA_AUTHORIZATION",
    default="",
    help="Set Authorization header (env: CAMUNDA_AUTHORIZATION).",
)
@click.pass_context
def main(ctx, url, authorization):
    ctx.obj = GlobalOptions(url=url, authorization=authorization)


@main.group(name="complete")
def complete():
    pass


def get_global_options(ctx: Context) -> GlobalOptions:
    if ctx.parent is not None:
        return get_global_options(ctx.parent)
    return GlobalOptions(
        url=ctx.params.get("url") or "",
        authorization=ctx.params.get("authorization") or "",
    )


def complete_instance_id(ctx: Context, param: Parameter, incomplete: str):
    options = get_global_options(ctx)
    incomplete = incomplete.split(":", 1)[0]
    with CamundaApiClient(options) as api_client:
        api_instance = generic_camunda_client.ProcessInstanceApi(api_client)
        instances = api_instance.get_process_instances()
        matches = [
            instance
            for instance in instances
            if not incomplete or instance.id.startswith(incomplete)
        ]
        if matches:
            return [
                f"{instance.id}:{instance.definition_id.rsplit(':', 1)[0]}"
                if len(matches) > 1
                else instance.id
                for instance in matches
            ]
        instances = api_instance.get_process_instances(
            process_definition_key=incomplete
        )
        matches = [
            instance
            for instance in instances
        ]
        return [
            f"{instance.id}:{instance.definition_id.rsplit(':', 1)[0]}"
            if len(matches) > 1
            else instance.id
            for instance in matches
        ]


def complete_task_id(ctx: Context, param: Parameter, incomplete: str):
    options = get_global_options(ctx)
    instance_id = ctx.params.get("instance_id") or ""
    with CamundaApiClient(options) as api_client:
        api_instance = generic_camunda_client.TaskApi(api_client)
        tasks = api_instance.get_tasks(process_instance_id=instance_id)
        return [
            task.id
            for task in tasks
            if not incomplete or task.id.startswith(incomplete)
        ]


@complete.command(name="user-task")
@click.argument("instance_id", required=False, shell_complete=complete_instance_id)
@click.argument("task_id", required=False, shell_complete=complete_task_id)
@click.pass_obj
def complete_user_task(options: GlobalOptions, instance_id, task_id):
    with CamundaApiClient(options) as api_client:
        api_instance = generic_camunda_client.TaskApi(api_client)
        print(api_instance.get_tasks())


@main.group(name="render")
@click.pass_obj
def render_group(obj):
    pass


@render_group.command(name="instance")
@click.argument("instance_id")
@click.argument("output_path", default="-")
@click.pass_obj
def render_instance(obj, instance_id: str, output_path: str):
    import pdb

    pdb.set_trace()
    with CamundaApiClient() as api_client:
        api_instance = generic_camunda_client.HistoricProcessInstanceApi(api_client)
        api_definition = generic_camunda_client.ProcessDefinitionApi(api_client)
        api_activities = generic_camunda_client.HistoricActivityInstanceApi(api_client)
        api_incidents = generic_camunda_client.IncidentApi(api_client)
        instance = api_instance.get_historic_process_instance(
            id=instance_id,
        )
        definition = api_definition.get_process_definition_bpmn20_xml(
            id=instance.process_definition_id
        )
        activities = api_activities.get_historic_activity_instances(
            process_instance_id=instance_id,
        )
        incidents = api_incidents.get_incidents(
            process_instance_id=instance_id,
        )
        with PlainTextApiClient() as text_api_client:
            api_job = generic_camunda_client.JobApi(text_api_client)
            api_task = generic_camunda_client.ExternalTaskApi(text_api_client)
            stacktraces = {
                incident.activity_id: api_job.get_stacktrace(
                    id=incident.configuration,
                )
                if incident.incident_type == "failedJob"
                else api_task.get_external_task_error_details(
                    id=incident.configuration,
                )
                if incident.incident_type == "failedExternalTask"
                else ""
                for incident in incidents
            }
        activities_json = json.dumps(
            [
                {
                    "activityId": activity.activity_id,
                    "startTime": activity.start_time.timestamp(),
                    "endTime": activity.end_time.timestamp()
                    if activity.end_time
                    else None,
                }
                for activity in activities
            ]
        )
        incidents_json = json.dumps(
            [
                {
                    "activityId": incident.activity_id,
                    "incidentMessage": incident.incident_message,
                }
                for incident in incidents
            ]
        )
        inject = f"""
        const activities = {activities_json};
        const incidents = {incidents_json};
        renderActivities(bpmnViewer, activities, incidents);
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            (Path(tmpdirname) / "input.bpmn").write_text(definition.bpmn20_xml)
            for asset in ASSETS:
                shutil.copy(str(asset), tmpdirname)
            skeleton_html = Path(tmpdirname) / "skeleton.html"
            skeleton_html.write_text(
                (Path(__file__).parent / "assets" / "skeleton.html")
                .read_text()
                .replace("/* PLACEHOLDER */", inject)
            )
            subprocess.call(
                [NODEJS_EXECUTABLE_PATH, str(tmpdirname)],
                env={"PUPPETEER_EXECUTABLE_PATH": PUPPETEER_EXECUTABLE_PATH},
            )
            time.sleep(1)
            output_png = (Path(tmpdirname) / "output.png").read_bytes()
            output_href = data_uri("image/png", output_png)
            template = chameleon.PageTemplateFile(
                Path(__file__).parent / "assets" / "instance.html"
            )
            html = template(
                title=instance_id,
                src=output_href,
                incidents=[
                    {
                        "message": incident.incident_message,
                        "detail": stacktraces.get(incident.activity_id) or "",
                    }
                    for incident in incidents
                ],
            ).strip()
            if output_path == "-":
                print(html)
            else:
                Path(output_path).write_text(html)


if __name__ == "__main__":
    main()
