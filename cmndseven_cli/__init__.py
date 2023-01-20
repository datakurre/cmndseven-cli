import base64
import chameleon
import click
import generic_camunda_client
import json
import shutil
import subprocess
import tempfile
import time
from generic_camunda_client.rest import ApiException
from pathlib import Path

ASSETS = [
    Path(__file__).parent / "assets" / "index.js",
    Path(__file__).parent / "assets" / "bpmn-viewer.production.min.js",
    Path(__file__).parent / "assets" / "puppeteer.production.min.js",
    Path(__file__).parent / "assets" / "skeleton.html",
]

NODEJS_EXECUTABLE_PATH = shutil.which("node")
PUPPETEER_EXECUTABLE_PATH = shutil.which("chrome") or shutil.which("chromium")


def data_uri(mimetype: str, data: bytes):
    return "data:{};base64,{}".format(mimetype, base64.b64encode(data).decode("utf-8"))


@click.group(help="Opinionated Camunda Platform 7 CLI")
def main():
    pass


@click.group(name="render")
def render_group():
    pass


@click.command(name="instance")
@click.argument("instance_id")
@click.argument("output_path", default="-")
def render_instance(instance_id, output_path):
    class PlainTextApiClient(generic_camunda_client.ApiClient):
        def select_header_accept(self, accepts):
            return "text/plain"

    configuration = generic_camunda_client.Configuration(
        host="http://localhost:8080/engine-rest"
    )

    with generic_camunda_client.ApiClient(configuration) as api_client:
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
        with PlainTextApiClient(configuration) as text_api_client:
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
                skeleton_html.read_text().replace("/* PLACEHOLDER */", inject)
            )
            subprocess.call(
                [NODEJS_EXECUTABLE_PATH, tmpdirname],
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


main.add_command(render_group)
render_group.add_command(render_instance)


if __name__ == "__main__":
    main()
