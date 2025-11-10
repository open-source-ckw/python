import json
from typing import Optional
import click
from nest.core.decorators.cli.cli_decorators import CliCommand, CliController
from src.ai.tenant.entity import AiTenantEntity
from src.ai.tenant.service import AiTenantService
from rich.console import Console
from rich.table import Table
from rich.json import JSON


"""
@CliController("tenant")
class AiTenantCli:
    def __init__(self, service: AiTenantService):
        self.service = service
    
    @CliCommand("hi")
    async def hi(self, 
                 id: click.Option(["--id"], type=int, help="Id of tenant", required=True) # type: ignore
                 ):
        resp: AiTenantEntity = await self.service.get_tenant(id)
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
    """

@CliController("tenant")
class AiTenantCli:
    def __init__(self, service: AiTenantService):
        self.service = service

    # --- parity with: GET /tenant/ ---
    @CliCommand("info")
    async def info(
        self,
        id: click.Option(["--id"], type=int, help="Tenant ID (default 1)", required=False)  # type: ignore
    ) -> None:
        tenant_id = id or 1
        resp: Optional[AiTenantEntity] = await self.service.get_tenant(tenant_id)
        if not resp:
            Console().print(f"[bold red]Error:[/] Tenant with ID {tenant_id} not found.")
            return
        data = resp.model_dump() if hasattr(resp, "model_dump") else resp.__dict__.copy()
        data.pop("_sa_instance_state", None)
        Console().print(JSON.from_data(data))

    # --- parity with: POST /tenant  (body: { "name": "Acme" }) ---
    @CliCommand("create")
    async def create(
        self,
        name: click.Option(["--name", "-n"], type=str, help="Tenant name", required=True)  # type: ignore
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            Console().print("[bold red]Error:[/] name is required")
            return
        created = await self.service.create_tenant(name.strip())
        data = created.model_dump() if hasattr(created, "model_dump") else created.__dict__.copy()
        data.pop("_sa_instance_state", None)
        Console().print("[bold green]Created[/]")
        Console().print(JSON.from_data(data))

    # --- parity with: GET /tenant/{tenant_id} ---
    @CliCommand("get")
    async def get(self, id: click.Option(["--id"], type=int, required=True)):  # type: ignore
        # This is working method and remain require some fix for printing json
        resp = await self.service.get_tenant(id)
        if not resp:
            Console().print(f"[bold red]Error:[/] Tenant with ID {id} not found.")
            return

        data = resp.model_dump() if hasattr(resp, "model_dump") else resp.__dict__.copy()
        # data.pop("_sa_instance_state", None)

        # Rich will internally call json.dumps(..., default=...)
        Console().print_json(data=data, default=str)   # converts datetime/date via str()

    # --- parity with: GET /tenant/search?name=Acme ---
    @CliCommand("search")
    async def search(
        self,
        name: click.Option(["--name", "-n"], type=str, help="Tenant name to search", required=True)  # type: ignore
    ) -> None:
        results = await self.service.search_tenants_by_name(name)
        rows = [
            (t.model_dump() if hasattr(t, "model_dump") else {**t.__dict__})
            for t in (results or [])
        ]
        for row in rows:
            row.pop("_sa_instance_state", None)
        Console().print(JSON.from_data(rows))

    # --- parity with: PUT /tenant/{tenant_id}/name  (body: { "name": "New Name" }) ---
    @CliCommand("update-name")
    async def update_name(
        self,
        id: click.Option(["--id"], type=int, help="Tenant ID", required=True),          # type: ignore
        name: click.Option(["--name", "-n"], type=str, help="New name", required=True) # type: ignore
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            Console().print("[bold red]Error:[/] name is required")
            return
        updated = await self.service.update_name(id, name.strip())
        if not updated:
            Console().print(f"[bold red]Error:[/] Tenant with ID {id} not found.")
            return
        data = updated.model_dump() if hasattr(updated, "model_dump") else updated.__dict__.copy()
        data.pop("_sa_instance_state", None)
        Console().print("[bold green]Updated[/]")
        Console().print(JSON.from_data(data))

    # --- parity with: PATCH /tenant/{tenant_id}  (body: partial JSON) ---
    @CliCommand("patch")
    async def patch(
        self,
        id: click.Option(["--id"], type=int, help="Tenant ID", required=True),                     # type: ignore
        data: click.Option(["--data"], type=str, help='JSON payload, e.g. \'{"name":"New"}\'', required=True)  # type: ignore
    ) -> None:
        try:
            payload = json.loads(data or "{}")
            if not isinstance(payload, dict):
                raise ValueError("payload must be a JSON object")
        except Exception as e:
            Console().print(f"[bold red]Error:[/] invalid JSON for --data ({e})")
            return

        updated = await self.service.patch_tenant(id, payload)
        if not updated:
            Console().print(f"[bold red]Error:[/] Tenant with ID {id} not found.")
            return

        out = updated.model_dump() if hasattr(updated, "model_dump") else updated.__dict__.copy()
        out.pop("_sa_instance_state", None)
        Console().print("[bold green]Patched[/]")
        Console().print(JSON.from_data(out))