from nest.core import Injectable
from typing import Annotated, List, Optional, Union
from strawberry.types import Info as StrawberryGraphQLResolveInfo
from starlette.datastructures import UploadFile

from libs.pynest_graphql import (
    Resolver,
    Query,
    Mutation,
    ResolveReference,
    Args,
    Context,
    Parent,
    Info as GqlInfo,
    Upload,
    BodySelection,
    UseGuards,
    Roles,
    Public,
    Cost,
)
from src.shared.api_endpoint_auth_file.dto import (
    ApiEndpointAuthFileDto,

    ApiEndpointAuthFileCreateDto,
    ApiEndpointAuthFileCreateInputDto,
    ApiEndpointAuthFileCreateOutputDto,
    ApiEndpointAuthFileCreateSelectionDto,

    ApiEndpointAuthFileFindDto,
    ApiEndpointAuthFileFindInputDto,
    ApiEndpointAuthFileFindOneByIdDto,
    ApiEndpointAuthFileFindOneByIdInputDto,
    ApiEndpointAuthFileFindOneByIdOutputDto,
    ApiEndpointAuthFileFindOneSelectionDto,
    ApiEndpointAuthFileFindOutputDto,
    ApiEndpointAuthFileFindOutputRowDto,
    ApiEndpointAuthFileFindSelectionDto,

    ApiEndpointAuthFileUpdateDto,
    ApiEndpointAuthFileUpdateInputDto,
    ApiEndpointAuthFileUpdateOutputDto,
    ApiEndpointAuthFileUpdateSelectionDto,

    ApiEndpointAuthFileSoftDeleteDto,
    ApiEndpointAuthFileSoftDeleteInputDto,
    ApiEndpointAuthFileSoftDeleteOutputDto,
    ApiEndpointAuthFileSoftDeleteSelectionDto,

    ApiEndpointAuthFileDeleteDto,
    ApiEndpointAuthFileDeleteInputDto,
    ApiEndpointAuthFileDeleteOutputDto,
    ApiEndpointAuthFileDeleteSelectionDto,

    ApiEndpointAuthFileRecoverDto,
    ApiEndpointAuthFileRecoverInputDto,
    ApiEndpointAuthFileRecoverOutputDto,
    ApiEndpointAuthFileRecoverSelectionDto,

    ApiEndpointAuthFileUpsertDto,
    ApiEndpointAuthFileUpsertInputDto,
    ApiEndpointAuthFileUpsertOutputDto,
    ApiEndpointAuthFileUpsertSelectionDto,

    ApiEndpointAuthFileSoftRemoveDto,
    ApiEndpointAuthFileSoftRemoveInputDto,
    ApiEndpointAuthFileSoftRemoveOutputDto,
    ApiEndpointAuthFileSoftRemoveSelectionDto,

    ApiEndpointAuthFileRestoreDto,
    ApiEndpointAuthFileRestoreInputDto,
    ApiEndpointAuthFileRestoreOutputDto,
    ApiEndpointAuthFileRestoreSelectionDto,

    ApiEndpointAuthFileRemoveDto,
    ApiEndpointAuthFileRemoveInputDto,
    ApiEndpointAuthFileRemoveOutputDto,
    ApiEndpointAuthFileRemoveSelectionDto,
    
    ApiEndpointAuthFileMarkAsMainDto,
    ApiEndpointAuthFileMarkAsMainInputDto,
    ApiEndpointAuthFileMarkAsMainOutputDto,
    ApiEndpointAuthFileMarkAsMainSelectionDto,

    ApiEndpointAuthFileRecordPositionDto,
    ApiEndpointAuthFileRecordPositionInputDto,
    ApiEndpointAuthFileRecordPositionOutputDto,
    ApiEndpointAuthFileRecordPositionSelectionDto,
    
    ApiEndpointAuthFileUploadDeleteDto,
    ApiEndpointAuthFileUploadDeleteInputDto,
    ApiEndpointAuthFileUploadDeleteOutputDto,
    ApiEndpointAuthFileUploadDeleteSelectionDto,
    ApiEndpointAuthFileUploadDto,
    ApiEndpointAuthFileUploadInputDto,
    ApiEndpointAuthFileUploadOutputDto,
    ApiEndpointAuthFileUploadSelectionDto,

    ApiEndpointAuthFileFileRelocationDto,
    ApiEndpointAuthFileFileRelocationInput,
    ApiEndpointAuthFileFileRelocationOutput,
    ApiEndpointAuthFileFileRelocationSelectionDto,
)
from src.shared.api_endpoint_auth_file.service import ApiEndpointAuthFileService


@Resolver(of=ApiEndpointAuthFileDto)
class ApiEndpointAuthFileResolver:
    def __init__(self, service: ApiEndpointAuthFileService):
        self.service = service

    # ████ find ████████████████████████████████████████
    @Query(
        name=ApiEndpointAuthFileFindDto.metaname,
        description=ApiEndpointAuthFileFindDto.metadesc
    )
    @Cost(5)  # contributes cost 5 to the query complexity budget
    async def find(
        self,
        ctx: Annotated[dict, Context()],
        filter: Annotated[ApiEndpointAuthFileFindInputDto, Args("filter")],
        selection: Annotated[ApiEndpointAuthFileFindSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> ApiEndpointAuthFileFindOutputDto:
        engine = self.service.factory.get_find_engine()
        return await engine.find(
            filter=filter,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ findOneById █████████████████████████████████
    @Query(
        name=ApiEndpointAuthFileFindOneByIdDto.metaname,
        description=ApiEndpointAuthFileFindOneByIdDto.metadesc
    )
    @Cost(1)  # contributes cost 5 to the query complexity budget
    async def find_one_by_id(
        self,
        ctx: Annotated[dict, Context()],
        input: Annotated[ApiEndpointAuthFileFindOneByIdInputDto, Args("input")],
        selection: Annotated[ApiEndpointAuthFileFindOneSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> ApiEndpointAuthFileFindOneByIdOutputDto:
        engine = self.service.factory.get_find_engine()
        return await engine.find_one_by_id(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ create ██████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileCreateDto.metaname,
        description=ApiEndpointAuthFileCreateDto.metadesc
    )
    async def create(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileCreateInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileCreateSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileCreateOutputDto]:
        engine = self.service.factory.get_create_engine()
        return await engine.create(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )

    # ████ update ██████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileUpdateDto.metaname,
        description=ApiEndpointAuthFileUpdateDto.metadesc
    )
    async def update(
        self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileUpdateInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileUpdateSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileUpdateOutputDto]:
        engine = self.service.factory.get_update_engine()
        return await engine.update(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )

    # ████ softDelete ██████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileSoftDeleteDto.metaname,
        description=ApiEndpointAuthFileSoftDeleteDto.metadesc
    )
    async def soft_delete(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileSoftDeleteInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileSoftDeleteSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileSoftDeleteOutputDto]:
        engine = self.service.factory.get_delete_engine()
        return await engine.soft_delete(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ delete ██████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileDeleteDto.metaname,
        description=ApiEndpointAuthFileDeleteDto.metadesc
    )
    async def delete(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileDeleteInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileDeleteSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileDeleteOutputDto]:
        engine = self.service.factory.get_delete_engine()
        return await engine.delete(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )



    # ████ restore █████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileRestoreDto.metaname,
        description=ApiEndpointAuthFileRestoreDto.metadesc
    )
    async def restore(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileRestoreInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileRestoreSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileRestoreOutputDto]:
        engine = self.service.factory.get_delete_engine()
        return await engine.restore(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ upsert ██████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileUpsertDto.metaname,
        description=ApiEndpointAuthFileUpsertDto.metadesc
    )
    async def upsert(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileUpsertInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileUpsertSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileUpsertOutputDto]:
        engine = self.service.factory.get_upsert_engine()
        return await engine.upsert(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ softRemove ██████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileSoftRemoveDto.metaname,
        description=ApiEndpointAuthFileSoftRemoveDto.metadesc
    )
    async def soft_remove(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileSoftRemoveInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileSoftRemoveSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileSoftRemoveOutputDto]:
        engine = self.service.factory.get_remove_engine()
        return await engine.soft_remove(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ remove ██████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileRemoveDto.metaname,
        description=ApiEndpointAuthFileRemoveDto.metadesc
    )
    async def remove(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileRemoveInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileRemoveSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileRemoveOutputDto]:
        engine = self.service.factory.get_remove_engine()
        return await engine.remove(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ recover █████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileRecoverDto.metaname,
        description=ApiEndpointAuthFileRecoverDto.metadesc
    )
    async def recover(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileRecoverInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileRecoverSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileRecoverOutputDto]:
        engine = self.service.factory.get_remove_engine()
        return await engine.recover(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ markAsMain ██████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileMarkAsMainDto.metaname,
        description=ApiEndpointAuthFileMarkAsMainDto.metadesc
    )
    async def mark_as_main(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileMarkAsMainInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileMarkAsMainSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileMarkAsMainOutputDto]:
        engine = self.service.factory.get_mark_as_main_engine()
        return await engine.mark_as_main(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )

    # ████ recordPosition ██████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileRecordPositionDto.metaname,
        description=ApiEndpointAuthFileRecordPositionDto.metadesc
    )
    async def record_position(self,
        ctx: Annotated[dict, Context()],
        input: Annotated[ApiEndpointAuthFileRecordPositionInputDto, Args("input")],
        selection: Annotated[ApiEndpointAuthFileRecordPositionSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileRecordPositionOutputDto]:
        engine = self.service.factory.get_record_position_engine()
        return await engine.record_position(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )
    

    # ████ upload ██████████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileUploadDto.metaname,
        description=ApiEndpointAuthFileUploadDto.metadesc
    )
    async def upload(
        self,
        ctx: Annotated[dict, Context()],
        attachment: Annotated[List[Upload], Args("attachment")],
        input: Annotated[ApiEndpointAuthFileUploadInputDto, Args("input")],
        selection: Annotated[ApiEndpointAuthFileUploadSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileUploadOutputDto]:
        engine = self.service.factory.get_upload_engine()
        return await engine.upload(
            attachment=attachment,
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )
    
    

    # ████ uploadDelete ████████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileUploadDeleteDto.metaname,
        description=ApiEndpointAuthFileUploadDeleteDto.metadesc
    )
    async def upload_delete(
        self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileUploadDeleteInputDto], Args("input")],
        selection: Annotated[ApiEndpointAuthFileUploadDeleteSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileUploadDeleteOutputDto]:
        engine = self.service.factory.get_upload_engine()
        return await engine.upload_delete(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )

    # ████ fileRelocation ██████████████████████████████
    @Mutation(
        name=ApiEndpointAuthFileFileRelocationDto.metaname,
        description=ApiEndpointAuthFileFileRelocationDto.metadesc
    )
    async def file_relocation(
        self,
        ctx: Annotated[dict, Context()],
        input: Annotated[List[ApiEndpointAuthFileFileRelocationInput], Args("input")],
        selection: Annotated[ApiEndpointAuthFileFileRelocationSelectionDto, BodySelection()],
        info: StrawberryGraphQLResolveInfo,
    ) -> List[ApiEndpointAuthFileFileRelocationOutput]:
        engine = self.service.factory.get_file_relocation_engine()
        return await engine.file_relocation(
            input=input,
            selection=selection,
            info=info,
            ctx=ctx,
        )


    # ████ SUPERGRAPH_FOREIGN_RELATION ██████████████████
    @ResolveReference()
    async def resolve_reference(
        self,
        entity: Annotated[ApiEndpointAuthFileFindOneByIdOutputDto, Parent()],
        ctx: Annotated[dict, Context()],
        info: StrawberryGraphQLResolveInfo,
    ) -> Optional[ApiEndpointAuthFileFindOneByIdOutputDto]:
        engine = self.service.factory.get_find_engine()
        return await engine.resolve_reference(
            entity=entity,
            info=info,
            ctx=ctx,
        )
