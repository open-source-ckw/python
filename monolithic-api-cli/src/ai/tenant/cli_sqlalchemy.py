import json
import click
from nest.core.decorators.cli.cli_decorators import CliCommand, CliController
from src.ai.tenant.entity import AiTenantEntity
from src.ai.tenant.service_sqlalchemy import AiTenantService
from rich.console import Console
from rich.table import Table
import json
from rich.json import JSON

@CliController("tenant")
class AiTenantCli:
    def __init__(self, service: AiTenantService):
        self.service = service
        
    
    @CliCommand("hi")
    async def hi(self, 
                 id: click.Option(["--id"], type=int, help="Id of tenant", required=True) # type: ignore
                 ):
        resp: AiTenantEntity = await self.service.FindOneById(id)
        
        """
        sample output of API in REST:
        {
            "tnt_name": "Thats End PVT. LTD.",
            "tnt_updated": null,
            "tnt_deleted": null,
            "tnt_created": "2025-09-17T20:26:36.751516+00:00",
            "tnt_id": 1
        }
        """
        rconsole = Console()
        
        if not resp:
            rconsole.print(f"[bold red]Error:[/] User with ID {id} not found.")
            return
        
        # simple print
        print(json.dumps(resp.__dict__, default=str))

        # formatted json
        data = resp.__dict__.copy()
        data.pop("_sa_instance_state", None)
        rconsole.print(JSON(json.dumps(data, default=str)))

        # Create a table for the single object
        table = Table(title=f"Tenant Information (ID: {resp.id})")
        table.add_column("Field", justify="right", style="cyan")
        table.add_column("Value", justify="left", style="magenta")

        # Convert the ORM object to a dictionary for easy iteration
        # You may need to adjust the attribute names based on your model
        data = {
            "ID": resp.id,
            "Name": resp.name,
            "Created": resp.created,
            # Add other fields here...
        }
        
        # Add a row for each key-value pair
        for key, value in data.items():
            table.add_row(key, str(value))
        
        rconsole.print(table)
