from typing import Any, Optional
from nest.core import Controller, Get, Post, Put, Patch  # adjust to your decorators
from src.shared.api_endpoint_auth_file.entity import ApiEndpointAuthFileEntity
from src.shared.api_endpoint_auth_file.service import ApiEndpointAuthFileService


@Controller("aepuf")
class ApiEndpointAuthFileController:
    def __init__(self, service: ApiEndpointAuthFileService):
        self.service = service

    