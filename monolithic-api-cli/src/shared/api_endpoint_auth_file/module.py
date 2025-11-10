from nest.core import Module

from src.shared.api_endpoint_auth_file.controller import ApiEndpointAuthFileController
from src.shared.api_endpoint_auth_file.factory import ApiEndpointAuthFileFactory
from src.shared.api_endpoint_auth_file.service import ApiEndpointAuthFileService


@Module(
    imports=[],
    controllers=[ApiEndpointAuthFileController],
    providers=[ApiEndpointAuthFileService, ApiEndpointAuthFileFactory],
    exports=[ApiEndpointAuthFileService],
    
)
class ApiEndpointAuthFileModule:
    pass
