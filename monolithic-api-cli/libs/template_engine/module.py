from nest.core import Module
from libs.template_engine.service import TemplateEngineService


@Module(
    controllers=[],
    providers=[TemplateEngineService],
)
class TemplateEngineModule:
    pass
