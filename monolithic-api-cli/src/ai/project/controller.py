from nest.core import Controller, Get
from src.ai.project.service import AiProjectService

@Controller("project")
class AiProjectController:
    def __init__(self, service: AiProjectService):
        self.service = service
    
    @Get("/")
    def hello(self):
        return self.service.hello()
