from nest.core.decorators.cli.cli_decorators import CliCommand, CliController
from nest.core import Controller, Get
from libs.jwt.http_guard import PublicRoute
from src.app_service import AppService
import click

@Controller("/")
class AppController:
    def __init__(self, service: AppService ):
        self.service = service

    @Get("/")
    @PublicRoute
    def get_app_info(self):
        info = self.service.get_app_info()
        return info

