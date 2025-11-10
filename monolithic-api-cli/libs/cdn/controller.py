from nest.core import Controller, Get

from libs.cdn.service import CdnService
from libs.jwt.http_guard import PublicRoute


@Controller("cdn")
class CdnController:
    def __init__(self, service: CdnService):
        self.service = service

    @Get("/t/{path:path}")
    @PublicRoute
    def tmp(self, path: str):
        return self.service.serve_tmp(path)

    @Get("/i/{path:path}")
    @PublicRoute
    def image(self, path: str):
        return self.service.serve_image(path)

    @Get("/u/{path:path}")
    @PublicRoute
    def upload(self, path: str):
        return self.service.serve_upload(path)
