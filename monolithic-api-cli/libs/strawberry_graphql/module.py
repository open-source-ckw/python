from nest.core import Module
from libs.strawberry_graphql.service import StrawberryGraphQLService

@Module(
    imports=[],
    providers=[StrawberryGraphQLService],
    exports=[StrawberryGraphQLService]
)
class StrawberryGraphQLModule:
    pass    