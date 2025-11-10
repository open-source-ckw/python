from typing import Any, MutableMapping, Optional, Sequence

from nest.core import Injectable
from strawberry.types import Info as StrawberryGraphQLResolveInfo

from libs.conf.service import ConfService
from libs.crud.factory import CrudFactory
from libs.libs_service import LibsService
from libs.log.service import LogService
from libs.sql_alchemy.service import SqlAlchemyService
from libs.image_processing.service import ImageProcessingService

from src.shared.api_endpoint_auth.entity import ApiEndpointAuthEntity
from src.shared.api_endpoint_auth.private.dto import (
    ApiEndpointAuthDto,
    
    ApiEndpointAuthCreateDto,
    ApiEndpointAuthCreateInputDto,
    ApiEndpointAuthCreateOutputDto,
    ApiEndpointAuthCreateSelectionDto,

    ApiEndpointAuthFindDto,
    ApiEndpointAuthFindInputDto,
    ApiEndpointAuthFindInputGroupByDto,
    ApiEndpointAuthFindInputSortOrderDto,
    ApiEndpointAuthFindInputWhereDto,
    ApiEndpointAuthFindOneByIdDto,
    ApiEndpointAuthFindOneByIdInputDto,
    ApiEndpointAuthFindOutputDto,
    ApiEndpointAuthFindOutputRowDto,
    ApiEndpointAuthFindSelectionDto,
    ApiEndpointAuthFindOneSelectionDto,

    ApiEndpointAuthUpdateDto,
    ApiEndpointAuthUpdateInputDto,
    ApiEndpointAuthUpdateInputSetsDto,
    ApiEndpointAuthUpdateInputWhereDto,
    ApiEndpointAuthUpdateOutputAffectedRowDto,
    ApiEndpointAuthUpdateOutputDto,
    ApiEndpointAuthUpdateSelectionDto,

    ApiEndpointAuthSoftDeleteDto,
    ApiEndpointAuthSoftDeleteInputDto,
    ApiEndpointAuthSoftDeleteInputWhereDto,
    ApiEndpointAuthSoftDeleteOutputDto,
    ApiEndpointAuthSoftDeleteSelectionDto,

    ApiEndpointAuthDeleteDto,
    ApiEndpointAuthDeleteInputDto,
    ApiEndpointAuthDeleteInputWhereDto,
    ApiEndpointAuthDeleteOutputDto,
    ApiEndpointAuthDeleteSelectionDto,

    ApiEndpointAuthRestoreDto,
    ApiEndpointAuthRestoreInputDto,
    ApiEndpointAuthRestoreInputWhereDto,
    ApiEndpointAuthRestoreOutputDto,
    ApiEndpointAuthRestoreSelectionDto,

    ApiEndpointAuthUpsertDto,
    ApiEndpointAuthUpsertInputRowDto,
    ApiEndpointAuthUpsertInputDto,
    ApiEndpointAuthUpsertOutputDto,
    ApiEndpointAuthUpsertSelectionDto,

    ApiEndpointAuthSoftRemoveDto,
    ApiEndpointAuthSoftRemoveInputDto,
    ApiEndpointAuthSoftRemoveInputWhereDto,
    ApiEndpointAuthSoftRemoveOutputAffectedRowDto,
    ApiEndpointAuthSoftRemoveOutputDto,
    ApiEndpointAuthSoftRemoveSelectionDto,

    ApiEndpointAuthRemoveDto,
    ApiEndpointAuthRemoveInputDto,
    ApiEndpointAuthRemoveInputWhereDto,
    ApiEndpointAuthRemoveOutputAffectedRowDto,
    ApiEndpointAuthRemoveOutputDto,
    ApiEndpointAuthRemoveSelectionDto,

    ApiEndpointAuthRecoverDto,
    ApiEndpointAuthRecoverInputDto,
    ApiEndpointAuthRecoverInputWhereDto,
    ApiEndpointAuthRecoverOutputAffectedRowDto,
    ApiEndpointAuthRecoverOutputDto,
    ApiEndpointAuthRecoverSelectionDto,

    ApiEndpointAuthMarkAsMainDto,
    ApiEndpointAuthMarkAsMainInputDto,
    ApiEndpointAuthMarkAsMainOutputDto,
    ApiEndpointAuthRecordPositionDto,
    ApiEndpointAuthRecordPositionInputDto,
    ApiEndpointAuthRecordPositionOutputDto,

    ApiEndpointAuthUploadDto,
    ApiEndpointAuthUploadInputDto,
    ApiEndpointAuthUploadOutputDto,
    ApiEndpointAuthUploadSelectionDto,
    ApiEndpointAuthUploadDeleteDto,
    ApiEndpointAuthUploadDeleteInputDto,
    ApiEndpointAuthUploadDeleteOutputDto,
    ApiEndpointAuthUploadDeleteSelectionDto,

    ApiEndpointAuthFileRelocationDto,
    ApiEndpointAuthFileRelocationInput,
    ApiEndpointAuthFileRelocationOutput,
    ApiEndpointAuthFileRelocationSelectionDto,
)

@Injectable
class ApiEndpointAuthFactory(CrudFactory[ApiEndpointAuthEntity, ApiEndpointAuthDto]):
    def __init__(
        self,
        db: SqlAlchemyService,
        
        conf: ConfService,
        log: LogService,
        library: LibsService,

        image_processing: ImageProcessingService,
    ) -> None:
        super().__init__(
            db=db,
            
            conf=conf,
            log=log,
            library=library,

            ENTITY=ApiEndpointAuthEntity,
            DTO=ApiEndpointAuthDto,

            image_processing=image_processing,
        )

        # Align log context with the factory name for structured logging.
        self.log = self.log.bind(service=self.__class__.__name__)

        # Register the find engine first so that downstream helpers can rely on it.
        self.find_engine = self.init_find_engine(
            FIND_DTO=ApiEndpointAuthFindDto,
            FIND_INPUT_WHERE_DTO=ApiEndpointAuthFindInputWhereDto,
            FIND_INPUT_SORT_ORDER_DTO=ApiEndpointAuthFindInputSortOrderDto,
            FIND_INPUT_GROUP_BY_DTO=ApiEndpointAuthFindInputGroupByDto,
            FIND_INPUT_DTO=ApiEndpointAuthFindInputDto,
            FIND_OUTPUT_ROWS_DTO=ApiEndpointAuthFindOutputRowDto,
            FIND_OUTPUT_PAGINATION_DTO=ApiEndpointAuthFindOutputDto,
            FIND_OUTPUT_DTO=ApiEndpointAuthFindOutputDto,
            FIND_SELECTION_DTO=ApiEndpointAuthFindSelectionDto,
            FIND_ONE_BY_ID_DTO=ApiEndpointAuthFindOneByIdDto,
            FIND_ONE_BY_ID_INPUT_DTO=ApiEndpointAuthFindOneByIdInputDto,
            FIND_ONE_SELECTION_DTO=ApiEndpointAuthFindOneSelectionDto,
        )

        # Register the create engine
        self.create_engine = self.init_create_engine(
            CREATE_DTO=ApiEndpointAuthCreateDto,
            CREATE_INPUT_DTO=ApiEndpointAuthCreateInputDto,
            CREATE_OUTPUT_DTO=ApiEndpointAuthCreateOutputDto,
            CREATE_SELECTION_DTO=ApiEndpointAuthCreateSelectionDto,
        )

        # Register the update engine
        self.update_engine = self.init_update_engine(
            UPDATE_DTO=ApiEndpointAuthUpdateDto,
            UPDATE_INPUT_WHERE_DTO=ApiEndpointAuthUpdateInputWhereDto,
            UPDATE_INPUT_SETS_DTO=ApiEndpointAuthUpdateInputSetsDto,
            UPDATE_INPUT_DTO=ApiEndpointAuthUpdateInputDto,
            UPDATE_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthUpdateOutputAffectedRowDto,
            UPDATE_OUTPUT_DTO=ApiEndpointAuthUpdateOutputDto,
            UPDATE_SELECTION_DTO=ApiEndpointAuthUpdateSelectionDto,
        )

        # Register the delete engine
        self.delete_engine = self.init_delete_engine(
            SOFT_DELETE_DTO=ApiEndpointAuthSoftDeleteDto,
            SOFT_DELETE_INPUT_WHERE_DTO=ApiEndpointAuthSoftDeleteInputWhereDto,
            SOFT_DELETE_INPUT_DTO=ApiEndpointAuthSoftDeleteInputDto,
            SOFT_DELETE_OUTPUT_DTO=ApiEndpointAuthSoftDeleteOutputDto,
            SOFT_DELETE_SELECTION_DTO=ApiEndpointAuthSoftDeleteSelectionDto,
            DELETE_DTO=ApiEndpointAuthDeleteDto,
            DELETE_INPUT_WHERE_DTO=ApiEndpointAuthDeleteInputWhereDto,
            DELETE_INPUT_DTO=ApiEndpointAuthDeleteInputDto,
            DELETE_OUTPUT_DTO=ApiEndpointAuthDeleteOutputDto,
            DELETE_SELECTION_DTO=ApiEndpointAuthDeleteSelectionDto,
            RESTORE_DTO=ApiEndpointAuthRestoreDto,
            RESTORE_INPUT_WHERE_DTO=ApiEndpointAuthRestoreInputWhereDto,
            RESTORE_INPUT_DTO=ApiEndpointAuthRestoreInputDto,
            RESTORE_OUTPUT_DTO=ApiEndpointAuthRestoreOutputDto,
            RESTORE_SELECTION_DTO=ApiEndpointAuthRestoreSelectionDto,
        )

        # Register the upsert engine
        self.upsert_engine = self.init_upsert_engine(
            UPSERT_DTO=ApiEndpointAuthUpsertDto,
            UPSERT_INPUT_ROW_DTO=ApiEndpointAuthUpsertInputRowDto,
            UPSERT_INPUT_DTO=ApiEndpointAuthUpsertInputDto,
            UPSERT_OUTPUT_DTO=ApiEndpointAuthUpsertOutputDto,
            UPSERT_SELECTION_DTO=ApiEndpointAuthUpsertSelectionDto,
        )

        # Register the remove engine
        self.remove_engine = self.init_remove_engine(
            SOFT_REMOVE_DTO=ApiEndpointAuthSoftRemoveDto,
            SOFT_REMOVE_INPUT_WHERE_DTO=ApiEndpointAuthSoftRemoveInputWhereDto,
            SOFT_REMOVE_INPUT_DTO=ApiEndpointAuthSoftRemoveInputDto,
            SOFT_REMOVE_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthSoftRemoveOutputAffectedRowDto,
            SOFT_REMOVE_OUTPUT_DTO=ApiEndpointAuthSoftRemoveOutputDto,
            SOFT_REMOVE_SELECTION_DTO=ApiEndpointAuthSoftRemoveSelectionDto,
            REMOVE_DTO=ApiEndpointAuthRemoveDto,
            REMOVE_INPUT_WHERE_DTO=ApiEndpointAuthRemoveInputWhereDto,
            REMOVE_INPUT_DTO=ApiEndpointAuthRemoveInputDto,
            REMOVE_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthRemoveOutputAffectedRowDto,
            REMOVE_OUTPUT_DTO=ApiEndpointAuthRemoveOutputDto,
            REMOVE_SELECTION_DTO=ApiEndpointAuthRemoveSelectionDto,
            RECOVER_DTO=ApiEndpointAuthRecoverDto,
            RECOVER_INPUT_WHERE_DTO=ApiEndpointAuthRecoverInputWhereDto,
            RECOVER_INPUT_DTO=ApiEndpointAuthRecoverInputDto,
            RECOVER_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthRecoverOutputAffectedRowDto,
            RECOVER_OUTPUT_DTO=ApiEndpointAuthRecoverOutputDto,
            RECOVER_SELECTION_DTO=ApiEndpointAuthRecoverSelectionDto,
        )

        # Register the mark-as-main engine
        self.mark_as_main_engine = self.init_mark_as_main_engine(
            MARK_AS_MAIN_DTO=ApiEndpointAuthMarkAsMainDto,
            MARK_AS_MAIN_INPUT_DTO=ApiEndpointAuthMarkAsMainInputDto,
            MARK_AS_MAIN_OUTPUT_DTO=ApiEndpointAuthMarkAsMainOutputDto,
        )

        # Register the record-position engine
        self.record_position_engine = self.init_record_position_engine(
            RECORD_POSITION_DTO=ApiEndpointAuthRecordPositionDto,
            RECORD_POSITION_INPUT_DTO=ApiEndpointAuthRecordPositionInputDto,
            RECORD_POSITION_OUTPUT_DTO=ApiEndpointAuthRecordPositionOutputDto,
        )

        # Register the upload engine
        self.upload_engine = self.init_upload_engine(
            UPLOAD_DTO=ApiEndpointAuthUploadDto,
            UPLOAD_INPUT_DTO=ApiEndpointAuthUploadInputDto,
            UPLOAD_OUTPUT_DTO=ApiEndpointAuthUploadOutputDto,
            UPLOAD_SELECTION_DTO=ApiEndpointAuthUploadSelectionDto,
            UPLOAD_DELETE_DTO=ApiEndpointAuthUploadDeleteDto,
            UPLOAD_DELETE_INPUT_DTO=ApiEndpointAuthUploadDeleteInputDto,
            UPLOAD_DELETE_OUTPUT_DTO=ApiEndpointAuthUploadDeleteOutputDto,
            UPLOAD_DELETE_SELECTION_DTO=ApiEndpointAuthUploadDeleteSelectionDto,
        )

        # Register the file-relocation engine
        self.file_relocation_engine = self.init_file_relocation_engine(
            FILE_RELOCATION_DTO=ApiEndpointAuthFileRelocationDto,
            FILE_RELOCATION_INPUT_DTO=ApiEndpointAuthFileRelocationInput,
            FILE_RELOCATION_OUTPUT_DTO=ApiEndpointAuthFileRelocationOutput,
            FILE_RELOCATION_SELECTION_DTO=ApiEndpointAuthFileRelocationSelectionDto,
        )

    # Sample usage of the create engine
    # async def create(
    #     self,
    #     input: ApiEndpointAuthCreateInputDto
    #     | Sequence[ApiEndpointAuthCreateInputDto],
    #     selection: Optional[ApiEndpointAuthCreateOutputDto] = None,
    #     info: Optional[StrawberryGraphQLResolveInfo] = None,
    #     ctx: Optional[MutableMapping[str, Any]] = None,
    #     etc: Optional[EtcProtocol] = None,
    # ) -> list[ApiEndpointAuthCreateOutputDto]:
    #     """Proxy helper for the create engine."""

    #     engine = self.get_create_engine()
    #     return await engine.create(
    #         input=input,
    #         selection=selection,
    #         info=info,
    #         ctx=ctx,
    #         etc=etc,
    #     )


__all__ = ["ApiEndpointAuthFactory"]
