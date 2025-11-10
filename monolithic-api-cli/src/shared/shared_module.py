from nest.core import Module
from src.shared.api_endpoint_auth.module import ApiEndpointAuthModule
from src.shared.api_endpoint_auth_file.module import ApiEndpointAuthFileModule
from src.shared.shared_service import SharedService

@Module(
    imports=[
        ApiEndpointAuthModule,
        ApiEndpointAuthFileModule,
    ],
    controllers=[],
    providers=[SharedService],
    exports=[
        SharedService,

        ApiEndpointAuthModule,
        ApiEndpointAuthFileModule,
    ],
)
class SharedModule:
    pass


@Module(
    imports=[
        
    ],
    controllers=[],
    providers=[SharedService],
    exports=[
        SharedService,

        
    ]
)
class SharedCliModule:
    pass