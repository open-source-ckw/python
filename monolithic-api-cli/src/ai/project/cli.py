import json
from nest.core.decorators.cli.cli_decorators import CliCommand, CliController
from src.ai.project.service import AiProjectService
from rich.console import Console
from rich.json import JSON
@CliController("jwt")
class AiProjectCli:
    def __init__(self, service: AiProjectService):
        self.service = service

    @CliCommand("get")
    def hello(self):
        resp = self.service.hello()
        rconsole = Console()
        # formatted json
        data = resp.copy()
        data.pop("_sa_instance_state", None)
        print(json.dumps(resp, default=str))
        rconsole.print(JSON(json.dumps(data, default=str)))
        
        