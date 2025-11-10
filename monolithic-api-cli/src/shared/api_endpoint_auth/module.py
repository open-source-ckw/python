
from nest.core import Module

from src.shared.api_endpoint_auth.factory import ApiEndpointAuthFactory
from src.shared.api_endpoint_auth.jwt import ApiEndpointAuthJwt
from src.shared.api_endpoint_auth.private.controller import (
    ApiEndpointAuthPrivateController,
)
from src.shared.api_endpoint_auth.public.controller import (
    ApiEndpointAuthPublicController,
)
from src.shared.api_endpoint_auth.repository import ApiEndpointAuthRepository
from src.shared.api_endpoint_auth.service import ApiEndpointAuthService

@Module(
    imports=[],
    controllers=[ApiEndpointAuthPrivateController, ApiEndpointAuthPublicController],
    providers=[
        ApiEndpointAuthRepository,
        ApiEndpointAuthFactory,
        ApiEndpointAuthJwt,
        ApiEndpointAuthService,
    ],
    exports=[ApiEndpointAuthService],
    
)
class ApiEndpointAuthModule:
    pass
