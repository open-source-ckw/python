from typing import Any, MutableMapping, Optional, Sequence

from nest.core import Injectable
from strawberry.types import Info as StrawberryGraphQLResolveInfo

from libs.conf.service import ConfService
from libs.crud.factory import CrudFactory
from libs.libs_service import LibsService
from libs.log.service import LogService
from libs.sql_alchemy.service import SqlAlchemyService
from libs.image_processing.service import ImageProcessingService

from src.shared.api_endpoint_auth_file.entity import ApiEndpointAuthFileEntity
from src.shared.api_endpoint_auth_file.dto import (
    ApiEndpointAuthFileDto,
    
    ApiEndpointAuthFileCreateDto,
    ApiEndpointAuthFileCreateInputDto,
    ApiEndpointAuthFileCreateOutputDto,
    ApiEndpointAuthFileCreateSelectionDto,

    ApiEndpointAuthFileFindDto,
    ApiEndpointAuthFileFindInputDto,
    ApiEndpointAuthFileFindInputGroupByDto,
    ApiEndpointAuthFileFindInputSortOrderDto,
    ApiEndpointAuthFileFindInputWhereDto,
    ApiEndpointAuthFileFindOneByIdDto,
    ApiEndpointAuthFileFindOneByIdInputDto,
    ApiEndpointAuthFileFindOutputDto,
    ApiEndpointAuthFileFindOutputRowDto,
    ApiEndpointAuthFileFindSelectionDto,
    ApiEndpointAuthFileFindOneSelectionDto,

    ApiEndpointAuthFileUpdateDto,
    ApiEndpointAuthFileUpdateInputDto,
    ApiEndpointAuthFileUpdateInputSetsDto,
    ApiEndpointAuthFileUpdateInputWhereDto,
    ApiEndpointAuthFileUpdateOutputAffectedRowDto,
    ApiEndpointAuthFileUpdateOutputDto,
    ApiEndpointAuthFileUpdateSelectionDto,

    ApiEndpointAuthFileSoftDeleteDto,
    ApiEndpointAuthFileSoftDeleteInputDto,
    ApiEndpointAuthFileSoftDeleteInputWhereDto,
    ApiEndpointAuthFileSoftDeleteOutputDto,
    ApiEndpointAuthFileSoftDeleteSelectionDto,

    ApiEndpointAuthFileDeleteDto,
    ApiEndpointAuthFileDeleteInputDto,
    ApiEndpointAuthFileDeleteInputWhereDto,
    ApiEndpointAuthFileDeleteOutputDto,
    ApiEndpointAuthFileDeleteSelectionDto,

    ApiEndpointAuthFileRestoreDto,
    ApiEndpointAuthFileRestoreInputDto,
    ApiEndpointAuthFileRestoreInputWhereDto,
    ApiEndpointAuthFileRestoreOutputDto,
    ApiEndpointAuthFileRestoreSelectionDto,

    ApiEndpointAuthFileUpsertDto,
    ApiEndpointAuthFileUpsertInputRowDto,
    ApiEndpointAuthFileUpsertInputDto,
    ApiEndpointAuthFileUpsertOutputDto,
    ApiEndpointAuthFileUpsertSelectionDto,

    ApiEndpointAuthFileSoftRemoveDto,
    ApiEndpointAuthFileSoftRemoveInputDto,
    ApiEndpointAuthFileSoftRemoveInputWhereDto,
    ApiEndpointAuthFileSoftRemoveOutputAffectedRowDto,
    ApiEndpointAuthFileSoftRemoveOutputDto,
    ApiEndpointAuthFileSoftRemoveSelectionDto,

    ApiEndpointAuthFileRemoveDto,
    ApiEndpointAuthFileRemoveInputDto,
    ApiEndpointAuthFileRemoveInputWhereDto,
    ApiEndpointAuthFileRemoveOutputAffectedRowDto,
    ApiEndpointAuthFileRemoveOutputDto,
    ApiEndpointAuthFileRemoveSelectionDto,

    ApiEndpointAuthFileRecoverDto,
    ApiEndpointAuthFileRecoverInputDto,
    ApiEndpointAuthFileRecoverInputWhereDto,
    ApiEndpointAuthFileRecoverOutputAffectedRowDto,
    ApiEndpointAuthFileRecoverOutputDto,
    ApiEndpointAuthFileRecoverSelectionDto,

    ApiEndpointAuthFileMarkAsMainDto,
    ApiEndpointAuthFileMarkAsMainInputDto,
    ApiEndpointAuthFileMarkAsMainOutputDto,
    ApiEndpointAuthFileRecordPositionDto,
    ApiEndpointAuthFileRecordPositionInputDto,
    ApiEndpointAuthFileRecordPositionOutputDto,

    ApiEndpointAuthFileUploadDto,
    ApiEndpointAuthFileUploadInputDto,
    ApiEndpointAuthFileUploadOutputDto,
    ApiEndpointAuthFileUploadSelectionDto,
    ApiEndpointAuthFileUploadDeleteDto,
    ApiEndpointAuthFileUploadDeleteInputDto,
    ApiEndpointAuthFileUploadDeleteOutputDto,
    ApiEndpointAuthFileUploadDeleteSelectionDto,

    ApiEndpointAuthFileFileRelocationDto,
    ApiEndpointAuthFileFileRelocationInput,
    ApiEndpointAuthFileFileRelocationOutput,
    ApiEndpointAuthFileFileRelocationSelectionDto,
)

@Injectable
class ApiEndpointAuthFileFactory(CrudFactory[ApiEndpointAuthFileEntity, ApiEndpointAuthFileDto]):
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

            ENTITY=ApiEndpointAuthFileEntity,
            DTO=ApiEndpointAuthFileDto,

            image_processing=image_processing,
        )

        # Align log context with the factory name for structured logging.
        self.log = self.log.bind(service=self.__class__.__name__)

        # Register the find engine first so that downstream helpers can rely on it.
        self.find_engine = self.init_find_engine(
            FIND_DTO=ApiEndpointAuthFileFindDto,
            FIND_INPUT_WHERE_DTO=ApiEndpointAuthFileFindInputWhereDto,
            FIND_INPUT_SORT_ORDER_DTO=ApiEndpointAuthFileFindInputSortOrderDto,
            FIND_INPUT_GROUP_BY_DTO=ApiEndpointAuthFileFindInputGroupByDto,
            FIND_INPUT_DTO=ApiEndpointAuthFileFindInputDto,
            FIND_OUTPUT_ROWS_DTO=ApiEndpointAuthFileFindOutputRowDto,
            FIND_OUTPUT_PAGINATION_DTO=ApiEndpointAuthFileFindOutputDto,
            FIND_OUTPUT_DTO=ApiEndpointAuthFileFindOutputDto,
            FIND_SELECTION_DTO=ApiEndpointAuthFileFindSelectionDto,
            FIND_ONE_BY_ID_DTO=ApiEndpointAuthFileFindOneByIdDto,
            FIND_ONE_BY_ID_INPUT_DTO=ApiEndpointAuthFileFindOneByIdInputDto,
            FIND_ONE_SELECTION_DTO=ApiEndpointAuthFileFindOneSelectionDto,
        )

        # Register the create engine
        self.create_engine = self.init_create_engine(
            CREATE_DTO=ApiEndpointAuthFileCreateDto,
            CREATE_INPUT_DTO=ApiEndpointAuthFileCreateInputDto,
            CREATE_OUTPUT_DTO=ApiEndpointAuthFileCreateOutputDto,
            CREATE_SELECTION_DTO=ApiEndpointAuthFileCreateSelectionDto,
        )

        # Register the update engine
        self.update_engine = self.init_update_engine(
            UPDATE_DTO=ApiEndpointAuthFileUpdateDto,
            UPDATE_INPUT_WHERE_DTO=ApiEndpointAuthFileUpdateInputWhereDto,
            UPDATE_INPUT_SETS_DTO=ApiEndpointAuthFileUpdateInputSetsDto,
            UPDATE_INPUT_DTO=ApiEndpointAuthFileUpdateInputDto,
            UPDATE_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthFileUpdateOutputAffectedRowDto,
            UPDATE_OUTPUT_DTO=ApiEndpointAuthFileUpdateOutputDto,
            UPDATE_SELECTION_DTO=ApiEndpointAuthFileUpdateSelectionDto,
        )

        # Register the delete engine
        self.delete_engine = self.init_delete_engine(
            SOFT_DELETE_DTO=ApiEndpointAuthFileSoftDeleteDto,
            SOFT_DELETE_INPUT_WHERE_DTO=ApiEndpointAuthFileSoftDeleteInputWhereDto,
            SOFT_DELETE_INPUT_DTO=ApiEndpointAuthFileSoftDeleteInputDto,
            SOFT_DELETE_OUTPUT_DTO=ApiEndpointAuthFileSoftDeleteOutputDto,
            SOFT_DELETE_SELECTION_DTO=ApiEndpointAuthFileSoftDeleteSelectionDto,
            DELETE_DTO=ApiEndpointAuthFileDeleteDto,
            DELETE_INPUT_WHERE_DTO=ApiEndpointAuthFileDeleteInputWhereDto,
            DELETE_INPUT_DTO=ApiEndpointAuthFileDeleteInputDto,
            DELETE_OUTPUT_DTO=ApiEndpointAuthFileDeleteOutputDto,
            DELETE_SELECTION_DTO=ApiEndpointAuthFileDeleteSelectionDto,
            RESTORE_DTO=ApiEndpointAuthFileRestoreDto,
            RESTORE_INPUT_WHERE_DTO=ApiEndpointAuthFileRestoreInputWhereDto,
            RESTORE_INPUT_DTO=ApiEndpointAuthFileRestoreInputDto,
            RESTORE_OUTPUT_DTO=ApiEndpointAuthFileRestoreOutputDto,
            RESTORE_SELECTION_DTO=ApiEndpointAuthFileRestoreSelectionDto,
        )

        # Register the upsert engine
        self.upsert_engine = self.init_upsert_engine(
            UPSERT_DTO=ApiEndpointAuthFileUpsertDto,
            UPSERT_INPUT_ROW_DTO=ApiEndpointAuthFileUpsertInputRowDto,
            UPSERT_INPUT_DTO=ApiEndpointAuthFileUpsertInputDto,
            UPSERT_OUTPUT_DTO=ApiEndpointAuthFileUpsertOutputDto,
            UPSERT_SELECTION_DTO=ApiEndpointAuthFileUpsertSelectionDto,
        )

        # Register the remove engine
        self.remove_engine = self.init_remove_engine(
            SOFT_REMOVE_DTO=ApiEndpointAuthFileSoftRemoveDto,
            SOFT_REMOVE_INPUT_WHERE_DTO=ApiEndpointAuthFileSoftRemoveInputWhereDto,
            SOFT_REMOVE_INPUT_DTO=ApiEndpointAuthFileSoftRemoveInputDto,
            SOFT_REMOVE_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthFileSoftRemoveOutputAffectedRowDto,
            SOFT_REMOVE_OUTPUT_DTO=ApiEndpointAuthFileSoftRemoveOutputDto,
            SOFT_REMOVE_SELECTION_DTO=ApiEndpointAuthFileSoftRemoveSelectionDto,
            REMOVE_DTO=ApiEndpointAuthFileRemoveDto,
            REMOVE_INPUT_WHERE_DTO=ApiEndpointAuthFileRemoveInputWhereDto,
            REMOVE_INPUT_DTO=ApiEndpointAuthFileRemoveInputDto,
            REMOVE_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthFileRemoveOutputAffectedRowDto,
            REMOVE_OUTPUT_DTO=ApiEndpointAuthFileRemoveOutputDto,
            REMOVE_SELECTION_DTO=ApiEndpointAuthFileRemoveSelectionDto,
            RECOVER_DTO=ApiEndpointAuthFileRecoverDto,
            RECOVER_INPUT_WHERE_DTO=ApiEndpointAuthFileRecoverInputWhereDto,
            RECOVER_INPUT_DTO=ApiEndpointAuthFileRecoverInputDto,
            RECOVER_OUTPUT_AFFECTED_ROWS_DTO=ApiEndpointAuthFileRecoverOutputAffectedRowDto,
            RECOVER_OUTPUT_DTO=ApiEndpointAuthFileRecoverOutputDto,
            RECOVER_SELECTION_DTO=ApiEndpointAuthFileRecoverSelectionDto,
        )

        # Register the mark-as-main engine
        self.mark_as_main_engine = self.init_mark_as_main_engine(
            MARK_AS_MAIN_DTO=ApiEndpointAuthFileMarkAsMainDto,
            MARK_AS_MAIN_INPUT_DTO=ApiEndpointAuthFileMarkAsMainInputDto,
            MARK_AS_MAIN_OUTPUT_DTO=ApiEndpointAuthFileMarkAsMainOutputDto,
        )

        # Register the record-position engine
        self.record_position_engine = self.init_record_position_engine(
            RECORD_POSITION_DTO=ApiEndpointAuthFileRecordPositionDto,
            RECORD_POSITION_INPUT_DTO=ApiEndpointAuthFileRecordPositionInputDto,
            RECORD_POSITION_OUTPUT_DTO=ApiEndpointAuthFileRecordPositionOutputDto,
        )

        # Register the upload engine
        self.upload_engine = self.init_upload_engine(
            UPLOAD_DTO=ApiEndpointAuthFileUploadDto,
            UPLOAD_INPUT_DTO=ApiEndpointAuthFileUploadInputDto,
            UPLOAD_OUTPUT_DTO=ApiEndpointAuthFileUploadOutputDto,
            UPLOAD_SELECTION_DTO=ApiEndpointAuthFileUploadSelectionDto,
            UPLOAD_DELETE_DTO=ApiEndpointAuthFileUploadDeleteDto,
            UPLOAD_DELETE_INPUT_DTO=ApiEndpointAuthFileUploadDeleteInputDto,
            UPLOAD_DELETE_OUTPUT_DTO=ApiEndpointAuthFileUploadDeleteOutputDto,
            UPLOAD_DELETE_SELECTION_DTO=ApiEndpointAuthFileUploadDeleteSelectionDto,
        )

        # Register the file-relocation engine
        self.file_relocation_engine = self.init_file_relocation_engine(
            FILE_RELOCATION_DTO=ApiEndpointAuthFileFileRelocationDto,
            FILE_RELOCATION_INPUT_DTO=ApiEndpointAuthFileFileRelocationInput,
            FILE_RELOCATION_OUTPUT_DTO=ApiEndpointAuthFileFileRelocationOutput,
            FILE_RELOCATION_SELECTION_DTO=ApiEndpointAuthFileFileRelocationSelectionDto,
        )

    # Sample usage of the create engine
    # async def create(
    #     self,
    #     input: ApiEndpointAuthFileCreateInputDto
    #     | Sequence[ApiEndpointAuthFileCreateInputDto],
    #     selection: Optional[ApiEndpointAuthFileCreateOutputDto] = None,
    #     info: Optional[StrawberryGraphQLResolveInfo] = None,
    #     ctx: Optional[MutableMapping[str, Any]] = None,
    #     etc: Optional[EtcProtocol] = None,
    # ) -> list[ApiEndpointAuthFileCreateOutputDto]:
    #     """Proxy helper for the create engine."""

    #     engine = self.get_create_engine()
    #     return await engine.create(
    #         input=input,
    #         selection=selection,
    #         info=info,
    #         ctx=ctx,
    #         etc=etc,
    #     )


__all__ = ["ApiEndpointAuthFileFactory"]