from nest.core.decorators.cli.cli_decorators import CliCommand, CliController
from nest.core import Controller
from src.app_service import AppService
import click
import datetime as dt

@CliController("app")
class AppCli:

    def __init__(self, service: AppService ):
        self.service = service

    @CliCommand("version")
    def version(self):
        self.service.version()
        
    @CliCommand("info")
    async def info(self):
        await self.service.info()

    
    @CliCommand("greet", help="Greet a user (PyNest-style options)")
    def greet(self, 
                name: click.Option(["-n", "--name"], type=str, help="Name to greet", required=True), # type: ignore
                at: click.Option(["--at"], type=click.DateTime(formats=["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M"]), help="Time to greet", default=None) = None # type: ignore
        ):
        #name: click.Option(["-n", "--name"], type=str, help="Name to greet", required=True), 
        #at: click.Option(["--at"], type=click.DateTime(formats=["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M"]), help="Time to greet", default=None) = None

        # to hide Pylance warning with parameters type need some work around as below, but it trigger other runtime error, so leaving it for future implementation
        #name: Annotated[str, click.Option(["-n", "--name"], type=str, required=True, help="Name to greet")], 
        #at: Annotated[Optional[dt.datetime], click.Option(["--at"], type=click.DateTime(formats=["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M"]), required=False, help="Time to greet")]
        
        # DI injects AppService by type; Click gives us parsed args
        """
        Greets a user at a given time.

        Args:
            name (str): The name of the user to greet.
            at (datetime | None): The time to greet the user at. If None, current time is used.

        Examples:
            >>> poetry run start-cli greet John --at "2023-07-25 14:30:00"
            Hello John! Time: 2023-07-25 14:30:00
            >>> poetry run start-cli greet John --at "14:30"
            Hello John! Time: 2023-07-25 14:30:00
        """
        ts = at or dt.datetime.now()
        self.service.info()  # demo: you still can use your service
        click.echo(click.style(f"Hello {name}! Time: {ts.strftime('%Y-%m-%d %H:%M:%S')}", fg="green"))


