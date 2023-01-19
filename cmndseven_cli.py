import click
import generic_camunda_client
import subprocess
import tempfile

from pathlib import Path
from generic_camunda_client.rest import ApiException


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
        instance = api_instance.get_historic_process_instance(
            id=instance_id,
        )
        definition = api_definition.get_process_definition_bpmn20_xml(
            id=instance.process_definition_id
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            path_bpmn = Path(Path(tmpdirname) / f"{instance.process_definition_key}.bpmn")
            path_bpmn.write_text(definition.bpmn20_xml)
            subprocess.call(
                [
                    "bpmn-to-image",
                    f"{path_bpmn}:{path_bpmn.with_suffix('.png')}",
                    "--no-title",
                    "--no-footer",
                ]
            )
            subprocess.call(
                [
                    "firefox",
                    f"{path_bpmn.with_suffix('.png')}"
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
