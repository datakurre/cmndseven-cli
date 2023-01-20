import click
import generic_camunda_client
import subprocess
import shutil
import tempfile
import json

from pathlib import Path
from generic_camunda_client.rest import ApiException

ASSETS = [
   Path(__file__).parent / "assets" / "index.js",
   Path(__file__).parent / "assets" / "bpmn-viewer.production.min.js",
   Path(__file__).parent / "assets" / "puppeteer.production.min.js",
   Path(__file__).parent / "assets" / "skeleton.html",
]


@click.group(help="Camunda Platform 7 CLI")
def main():
    pass


@click.group(name="render")
def render_group():
    pass


@click.command(name="instance")
@click.argument("instance_id")
def render_instance(instance_id):
    configuration = generic_camunda_client.Configuration(
        host = "http://localhost:8080/engine-rest"
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
        activities_json = json.dumps([
            {
            "activityId": activity.activity_id,
            "startTime": activity.start_time.timestamp(),
            "endTime": activity.end_time.timestamp() if activity.end_time else None
            } for activity in activities
        ])
        incidents_json = json.dumps([
            {
            "activityId": incident.activity_id,
            "incidentMessage": incident.incident_message
            } for incident in incidents
        ])
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
            skeleton_html.write_text(skeleton_html.read_text().replace("/* PLACEHOLDER */", inject))
            subprocess.call(
                [
                    "node",
                    tmpdirname
                ],
            )
            subprocess.call(
                [
                    "firefox",
                    Path(tmpdirname) / "output.png"
                ]
            )
            import time
            time.sleep(2)

#       activities = api_activities.get_historic_activity_instances(
#           process_instance_id=instance_id,
#       )
#       print(activities)


main.add_command(render_group)
render_group.add_command(render_instance)


if __name__ == '__main__':
    main()
