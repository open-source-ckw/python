from nest.core import Module
from src.ai.project.cli import AiProjectCli
from src.ai.project.controller import AiProjectController
from src.ai.project.service import AiProjectService


@Module(
    controllers=[AiProjectController],
    providers=[AiProjectService],
)
class AiProjectModule:
    pass



@Module(
    controllers=[AiProjectCli],
    providers=[AiProjectService],
)
class AiProjectCliModule:
    pass
