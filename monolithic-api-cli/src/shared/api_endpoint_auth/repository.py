"""Repository for ApiEndpointAuth domain objects."""
from nest.core import Injectable

from libs.sql_alchemy.repository import SqlAlchemyRepository
from libs.sql_alchemy.service import SqlAlchemyService

from src.shared.api_endpoint_auth.entity import ApiEndpointAuthEntity
from src.shared.api_endpoint_auth.private.dto import ApiEndpointAuthDto


@Injectable
class ApiEndpointAuthRepository(
    SqlAlchemyRepository[ApiEndpointAuthEntity, ApiEndpointAuthDto]
):
    """Application-facing repository for API endpoint auth records."""

    def __init__(self, db: SqlAlchemyService) -> None:
        super().__init__(
            db,
            entity_cls=ApiEndpointAuthEntity,
            dto_cls=ApiEndpointAuthDto,
        )


__all__ = ["ApiEndpointAuthRepository"]
