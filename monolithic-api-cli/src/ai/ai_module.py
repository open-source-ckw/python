from nest.core import Module
from src.ai.ai_service import AiService
from src.ai.project.module import AiProjectCliModule, AiProjectModule

@Module(
    imports=[
        AiProjectModule
    ],
    controllers=[],
    providers=[AiService],
    exports=[
        AiService,
        AiProjectModule
    ]
)
class AiModule:
    pass



@Module(
    imports=[
        AiProjectCliModule,
    ],
    controllers=[],
    providers=[AiService],
    exports=[
        AiService,
        AiProjectCliModule,
    ]
)
class AiCliModule:
    pass
