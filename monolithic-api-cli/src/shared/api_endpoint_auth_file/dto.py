# src/shared/api_endpoint_auth_file/dto.py
from datetime import datetime
from pathlib import Path
from libs.crud.constant import CREATE_ARTEFACT, CrudMeta
from libs.crud.decorator import CreateDateField, DeleteDateField, IsNotEntityField, MarkAsMainField, RecordPositionField, UpdateDateField, UploadField, UrlSlugField
from libs.crud.dto.affected_dto import AffectedDto
from libs.crud.dto.dto import Dto, DtoModel
from libs.crud.dto.file_relocation_dto import FileRelocationInputDto, FileRelocationOutputDto
from libs.crud.dto.find_operator_dto import FindOperatorDto
from libs.crud.dto.id_input_dto import IdInputDto
from libs.crud.dto.mark_as_main_dto import MarkAsMainInputDto, MarkAsMainOutputDto
from libs.crud.dto.pagination_dto import FindInputPaginationOptionsDto, FindOutputPaginationOptionsDto
from libs.crud.dto.record_postion_dto import RecordPositionInputDto, RecordPositionOutputDto
from libs.crud.dto.sort_option_dto import SortOrderOptionDto
from libs.crud.dto.upload_file_access_url_dto import UploadFileAccessUrlDto
from libs.crud.dto.upload_input_dto import UploadDeleteInputDto, UploadDeleteOutputDto, UploadInputDto, UploadOutputDto
from libs.crud.dto.upsert_dto import UpsertOutputProcessStatusDto
from libs.crud.dto.with_deleted_dto import WithDeletedInputDto
from typing import ClassVar, List, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field, computed_field
from libs.pynest_graphql.dto_composition import BoolType, InputType, ObjectType, PartialType, IntersectionType
from src.shared.api_endpoint_auth_file.enum import ApiEndpointAuthFileMarkAsMainFieldEnum, ApiEndpointAuthFileUploadFileFieldEnum

if TYPE_CHECKING:
    from src.shared.api_endpoint_auth.private.dto import ApiEndpointAuthDto, ApiEndpointAuthFindInputWhereDto 

"""
[done] change file path at line 1
[done] Fine "api_endpoint_auth_file" Replace "your_module_name"
[done] Find "ApiEndpointAuthFile" Replace "YourModuleName"
[done] ApiEndpointAuthFileDto: setup entire dto as per entity
[done] ApiEndpointAuthFileFindInputWhereDto: change all fields as per entity also adjjust relation fields
[done] ApiEndpointAuthFileFindInputGroupByDto: change all fields as per entity
[done] ApiEndpointAuthFileFindInputSortOrderDto: change all fields as per entity
[done] ApiEndpointAuthFileCreateInputDto: change all fields as per entity
[done] ApiEndpointAuthFileUpsertInputDto: need to change conflictResolveFields
[done] MarkAsMainCommonInputDto: need to change ApiEndpointAuthFileMarkAsMainFieldEnum
[done] UploadFileFieldInputDto: need to change ApiEndpointAuthFileUploadFileFieldEnum
"""

# █████████████████████████████████████████████████████████████
# ██ DO NOT CHANGE IN THIS FILE IT WILL CRASH THE APP        ██
# █████████████████████████████████████████████████████████████

@ObjectType
class ApiEndpointAuthFileDto(Dto):
    # Setup main DTO
    metaname: ClassVar[str] = None # trigger auto generate by removing *Entity suffix from class name
    metadesc: ClassVar[str] = "API acceess users, managed by API webmaster."
    
    # False: disabled | None: auto generate | set custom path | "+path": path start with + suffix/attch to auto generated path
    uploaddir: ClassVar[str | bool] = "aepufile"
    recorddir: ClassVar[str | bool] = None

    id: Optional[int] = Field(
        default=None,
        title="Unique ID in system",
        description="Primary key (IDENTITY).",
    )

    aepu_id: Optional[int] = Field(
        default=None,
        title="Foreign key relation",
        description="FK to ApiEndpointAuthEntity.id",
    )

    # multi file upload example | for single file upload try check _api_endpoint_auth
    file: Optional[str] = UploadField(
        ref_id_field="aepu_id",
        ref_relation_field="fr_api_endpoint_auth", # used for multiple file upload for same record in another table
        access_url_field="file_url",
        upload_dir=Path("{{ref_id}}"), 
        valid_file_format = [
            # Images
            "jpg", "jpeg", "png", "svg", "gif", "webp", "bmp", "tiff", "ico", "heic",
            
            # Documents
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf", "odt", "ods", "odp", "csv", "md",
            
            # Audio
            "mp3", "wav", "ogg", "m4a", "flac", "aac", "wma",
            
            # Video
            "mp4", "mov", "avi", "mkv", "webm", "wmv", "flv", "mpeg", "3gp",
            
            # Archives / Compressed
            "zip", "rar", "7z", "tar", "gz", "bz2",
            
            # Code / Data
            "json", "xml", "yml", "yaml", "ini", "log",
            
            # Fonts
            "ttf", "otf", "woff", "woff2"
        ],
        valid_mime_type = [
            # Images
            "image/jpeg", "image/png", "image/svg+xml", "image/gif", "image/webp",
            "image/bmp", "image/tiff", "image/x-icon", "image/heic",

            # Documents
            "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain", "application/rtf", "application/vnd.oasis.opendocument.text",
            "application/vnd.oasis.opendocument.spreadsheet", "application/vnd.oasis.opendocument.presentation",
            "text/csv", "text/markdown",

            # Audio
            "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/flac", "audio/aac", "audio/x-ms-wma",

            # Video
            "video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska",
            "video/webm", "video/x-ms-wmv", "video/x-flv", "video/mpeg", "video/3gpp",

            # Archives / Compressed
            "application/zip", "application/x-rar-compressed", "application/x-7z-compressed",
            "application/x-tar", "application/gzip", "application/x-bzip2",

            # Code / Data
            "application/json", "application/xml", "text/yaml", "application/x-yaml",
            "text/ini", "text/x-log",

            # Fonts
            "font/ttf", "font/otf", "font/woff", "font/woff2"
        ],
        max_file_size=5 * 1024 * 1024, # 5 MB
        req_max_count=5,

        default=None,
        max_length=255,
        title="Api user file",
        description="File upload for Api user, max 5 files at a time.",
    )
    
    file_url: Optional[UploadFileAccessUrlDto] = IsNotEntityField(
        UploadFileAccessUrlDto,
        default=None,
        title="Api user file URL",
        description="Derived public URL for the stored file.",
    )
    
    # @computed_field(
    #     title="Api user file URL",
    #     description="Derived public URL for the stored file.",
    #     return_type=Optional[str]
    # )
    # @property
    # def file_url(self) -> Optional[str]:
    #     if not self.file:
    #         return None
    #     return f"/profiles/{self.file}"

    created: Optional[datetime] = CreateDateField(
        default=datetime.now(),
        title="Record created",
        description="Record created date time.",
    )

    updated: Optional[datetime] = UpdateDateField(
        default=None,
        title="Record last updated",
        description="Record last updated date time. Update can be any. | null: no | date_time: yes  last action at",
    )

    deleted: Optional[datetime] = DeleteDateField(
        default=None,
        title="Record removed",
        description="When record is soft deleted or soft removed, date-time will be saved otherwise null to indicate record is not deleted. | null: no | date_time: yes  last action at",
    )

    # If you use this then you need to set `model_post_init`
    # file_url: Optional[str] = IsNotEntityField(
    #     pytype=str,
        
    #     default=None,
    #     title="Api user file URL",
    #     description="Derived public URL for the stored file.",
    # )

    # Another way porocess virtual fields in single hook
    # Virtual field processing hook method, execute once per initialization. if you mutate attributes later, you’ll need to handle those updates yourself.
    # def model_post_init(self, __context):
    #     super().model_post_init(__context)
    #     # add conditions to process the required fields and set output
    #     if self.file:
    #         object.__setattr__(self, "file_url", f"/profiles/{self.file}")
    #     else:
    #         object.__setattr__(self, "file_url", None)

    # ████ INTERNAL RELATIONS ████████████████████████████████████████████████

    fr_api_endpoint_auth: Optional["ApiEndpointAuthDto"] = Field(
        default=None,
        title="Api user",
        description="Parent API auth record that owns this file.",
    )

    # ████ EXTERNAL RELATIONS ████████████████████████████████████████████████



# █████████████████████████████████████████████████████████████
# █ FIND DTO ██████████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileFindDto(Dto):
    metaname: ClassVar[str]  = None
    metadesc: ClassVar[str]  = CrudMeta.find_metadesc


# ████ FIND INPUT DTO █████████████████████████████████████████

@InputType
class ApiEndpointAuthFileFindInputWhereDto(DtoModel):
    # use only fields which are declared in Entity class otherwise it will raise error
    id: Optional[FindOperatorDto] = Field(default=None, description="Filter by id using a single operator")
    aepu_id: Optional[FindOperatorDto] = Field(default=None, description="Filter by auth id using a single operator")
    file: Optional[FindOperatorDto] = Field(default=None, description="Filter by file using a single operator")

    created: Optional[FindOperatorDto] = Field(default=None, description="Filter by created using a single operator")
    updated: Optional[FindOperatorDto] = Field(default=None, description="Filter by updated using a single operator")
    deleted: Optional[FindOperatorDto] = Field(default=None, description="Filter by deleted using a single operator")

    # ████ FR_ WHERE: INTERNAL RELATIONS WHERE ████████████████████
    fr_api_endpoint_auth: Optional["ApiEndpointAuthFindInputWhereDto"] = Field(
        default=None,
        title="Find by api user",
        description="Find using parent API auth record that owns this file.",
    )
    
@InputType
class ApiEndpointAuthFileFindInputGroupByDto(DtoModel):
    # use only fields which are declared in Entity class otherwise it will raise error
    id: Optional[bool] = Field(default=None, description="Group by id")
    aepu_id: Optional[bool] = Field(default=None, description="Group by auth id")
    file: Optional[bool] = Field(default=None, description="Group by file")
    
    created: Optional[bool] = Field(default=None, description="Group by created")
    updated: Optional[bool] = Field(default=None, description="Group by updated")
    deleted: Optional[bool] = Field(default=None, description="Group by deleted")


@InputType
class ApiEndpointAuthFileFindInputSortOrderDto(DtoModel):
    # use only fields which are declared in Entity class otherwise it will raise error
    id: Optional[SortOrderOptionDto] = Field(default=None, description="Sort by id")
    aepu_id: Optional[SortOrderOptionDto] = Field(default=None, description="Sort by auth id")
    file: Optional[SortOrderOptionDto] = Field(default=None, description="Sort by file")
    
    created: Optional[SortOrderOptionDto] = Field(default=None, description="Sort by created")
    updated: Optional[SortOrderOptionDto] = Field(default=None, description="Sort by updated")
    deleted: Optional[SortOrderOptionDto] = Field(default=None, description="Sort by deleted")
    

@InputType
class ApiEndpointAuthFileFindInputDto(IntersectionType(FindInputPaginationOptionsDto, WithDeletedInputDto)):
    where: Optional[List[ApiEndpointAuthFileFindInputWhereDto]] = Field(default_factory=list, description="Where clause for filtering records")
    group_by: Optional[ApiEndpointAuthFileFindInputGroupByDto] = Field(default=None, description="Group by clause for filtering records")
    order_by: Optional[ApiEndpointAuthFileFindInputSortOrderDto] = Field(default=None, description="Order clause for sorting records")


# ████ FIND OUTPUT DTO ████████████████████████████████████████
@ObjectType
class ApiEndpointAuthFileFindOutputRowDto(ApiEndpointAuthFileDto):
    pass

@ObjectType
class ApiEndpointAuthFileFindOutputDto(FindOutputPaginationOptionsDto):
    rows: List[ApiEndpointAuthFileFindOutputRowDto] = Field(default_factory=list, description="List of found rows") 
    
class ApiEndpointAuthFileFindSelectionDto(BoolType(ApiEndpointAuthFileFindOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ FIND ONE BY ID DTO ████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileFindOneByIdDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.findonebyid_metadesc

# ████ FIND ONE BY ID INPUT DTO ███████████████████████████████

@InputType
class ApiEndpointAuthFileFindOneByIdInputDto(IdInputDto):
    pass

# ████ FIND ONE BY ID OUTPUT DTO ███████████████████████████████
@ObjectType
class ApiEndpointAuthFileFindOneByIdOutputDto(ApiEndpointAuthFileFindOutputRowDto):
    pass

class ApiEndpointAuthFileFindOneSelectionDto(BoolType(ApiEndpointAuthFileFindOneByIdOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ CREATE DTO ████████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileCreateDto(ApiEndpointAuthFileDto):
    metaname: ClassVar[str] = ApiEndpointAuthFileDto.crud_metaname(CREATE_ARTEFACT)
    metadesc: ClassVar[str] = CrudMeta.create_metadesc
    

# ████ CREATE INPUT DTO ███████████████████████████████████████

@InputType
class ApiEndpointAuthFileCreateInputDto(ApiEndpointAuthFileCreateDto):
    # Change the inherited DTO as needed: ApiEndpointAuthFileCreateDto, ApiEndpointAuthFileDto, ApiEndpointAuthFileDto
    # Only the fields listed below will be included; metadata is inherited and merged from entity
    aepu_id: int
    file: str


# ████ CREATE OUTPUT DTO ██████████████████████████████████████

@ObjectType
class ApiEndpointAuthFileCreateOutputDto(ApiEndpointAuthFileFindOutputRowDto):
    # example extra field can be added as require
    # ext_field: Optional[str] = Field(default='Extra Test')
    pass
    
class ApiEndpointAuthFileCreateSelectionDto(BoolType(ApiEndpointAuthFileCreateOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ UPDATE DTO ████████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileUpdateDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.update_metadesc

# ████ UPDATE INPUT DTO ███████████████████████████████████████

@InputType
class ApiEndpointAuthFileUpdateInputWhereDto(PartialType(ApiEndpointAuthFileFindInputWhereDto)):
    pass

@InputType
class ApiEndpointAuthFileUpdateInputSetsDto(PartialType(ApiEndpointAuthFileCreateInputDto)):
    pass

@InputType
class ApiEndpointAuthFileUpdateInputDto(WithDeletedInputDto):
    where: List[ApiEndpointAuthFileUpdateInputWhereDto] = Field(..., description="Where clause to apply update on specific records")
    sets: ApiEndpointAuthFileUpdateInputSetsDto = Field(..., description="Sets clause for updating records")

# ████ UPDATE OUTPUT DTO ██████████████████████████████████████

class ApiEndpointAuthFileUpdateOutputAffectedRowDto(ApiEndpointAuthFileFindOutputRowDto):
    pass

class ApiEndpointAuthFileUpdateOutputDto(AffectedDto):
    affected_rows: List[ApiEndpointAuthFileUpdateOutputAffectedRowDto] = Field(default_factory=list, description="List of affected rows during update operation")

class ApiEndpointAuthFileUpdateSelectionDto(BoolType(ApiEndpointAuthFileUpdateOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ SOFT DELETE DTO ███████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileSoftDeleteDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.softdelete_metadesc

# ████ SOFT DELETE INPUT DTO ██████████████████████████████████

class ApiEndpointAuthFileSoftDeleteInputWhereDto(PartialType(ApiEndpointAuthFileFindInputWhereDto)):
    pass

class ApiEndpointAuthFileSoftDeleteInputDto(DtoModel):
    where: List[ApiEndpointAuthFileSoftDeleteInputWhereDto] = Field(..., description="Where clause to apply soft delete on specific records")
    pass

# ████ SOFT DELETE OUTPUT DTO ██████████████████████████████████

class ApiEndpointAuthFileSoftDeleteOutputDto(AffectedDto):
    pass

class ApiEndpointAuthFileSoftDeleteSelectionDto(BoolType(ApiEndpointAuthFileSoftDeleteOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ DELETE DTO ████████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileDeleteDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.delete_metadesc

# ████ DELETE INPUT DTO ███████████████████████████████████████

class ApiEndpointAuthFileDeleteInputWhereDto(PartialType(ApiEndpointAuthFileFindInputWhereDto)):
    pass

class ApiEndpointAuthFileDeleteInputDto(DtoModel):
    where: List[ApiEndpointAuthFileDeleteInputWhereDto] = Field(..., description="Where clause to apply delete on specific records")
    pass

# ████ DELETE OUTPUT DTO ██████████████████████████████████████

class ApiEndpointAuthFileDeleteOutputDto(AffectedDto):
    pass

class ApiEndpointAuthFileDeleteSelectionDto(BoolType(ApiEndpointAuthFileDeleteOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ RESTORE DTO ███████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileRestoreDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.restore_metadesc

# ████ RESTORE INPUT DTO ██████████████████████████████████████

class ApiEndpointAuthFileRestoreInputWhereDto(PartialType(ApiEndpointAuthFileFindInputWhereDto)):
    pass

class ApiEndpointAuthFileRestoreInputDto(DtoModel):
    where: List[ApiEndpointAuthFileRestoreInputWhereDto] = Field(..., description="Where clause to apply restore on specific records")
    pass


# ████ RESTORE OUTPUT DTO █████████████████████████████████████

class ApiEndpointAuthFileRestoreOutputDto(AffectedDto):
    pass

class ApiEndpointAuthFileRestoreSelectionDto(BoolType(ApiEndpointAuthFileRestoreOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ UPSERT DTO ████████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileUpsertDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.upsert_metadesc

# ████ UPSERT INPUT DTO ███████████████████████████████████████

@InputType
class ApiEndpointAuthFileUpsertInputRowDto(ApiEndpointAuthFileCreateInputDto):
    id: Optional[int] = Field(
        default=None,
        description="ID of the record to update or use for create",
    )
    pass


@InputType
class ApiEndpointAuthFileUpsertInputDto(WithDeletedInputDto):
    rows: List[ApiEndpointAuthFileUpsertInputRowDto] = Field(
        ...,
        description="Sets clause for upserting records",
    )

    # List of fields to use for conflict resolution during create
    conflictResolveFields: ClassVar[List[Union[str, List[str]]]] = ["id"]
    
    

# ████ UPSERT OUTPUT DTO ███████████████████████████████████████

class ApiEndpointAuthFileUpsertOutputDto(IntersectionType(ApiEndpointAuthFileCreateOutputDto, UpsertOutputProcessStatusDto)):
    pass 

class ApiEndpointAuthFileUpsertSelectionDto(BoolType(ApiEndpointAuthFileUpsertOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ SOFT REMOVE DTO ███████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileSoftRemoveDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.softremove_metadesc

# ████ SOFT REMOVE INPUT DTO ██████████████████████████████████

class ApiEndpointAuthFileSoftRemoveInputWhereDto(PartialType(ApiEndpointAuthFileFindInputWhereDto)):
    pass

class ApiEndpointAuthFileSoftRemoveInputDto(DtoModel):
    where: List[ApiEndpointAuthFileSoftRemoveInputWhereDto] = Field(..., description="Where clause to apply soft remove on specific records")


# ████ SOFT REMOVE OUTPUT DTO █████████████████████████████████

class ApiEndpointAuthFileSoftRemoveOutputAffectedRowDto(ApiEndpointAuthFileFindOutputRowDto):
    pass

class ApiEndpointAuthFileSoftRemoveOutputDto(AffectedDto):
    affected_rows: List[ApiEndpointAuthFileSoftRemoveOutputAffectedRowDto] = Field(default_factory=list, description="List of affected rows during soft remove operation")

class ApiEndpointAuthFileSoftRemoveSelectionDto(BoolType(ApiEndpointAuthFileSoftRemoveOutputDto)):
    pass



# █████████████████████████████████████████████████████████████
# █ REMOVE DTO ████████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileRemoveDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.remove_metadesc

# ████ REMOVE INPUT DTO ███████████████████████████████████████

class ApiEndpointAuthFileRemoveInputWhereDto(PartialType(ApiEndpointAuthFileFindInputWhereDto)):
    pass

class ApiEndpointAuthFileRemoveInputDto(DtoModel):
    where: List[ApiEndpointAuthFileRemoveInputWhereDto] = Field(..., description="Where clause to apply remove on specific records")


# ████ REMOVE OUTPUT DTO █████████████████████████████████████

class ApiEndpointAuthFileRemoveOutputAffectedRowDto(ApiEndpointAuthFileFindOutputRowDto):
    pass

class ApiEndpointAuthFileRemoveOutputDto(AffectedDto):
    affected_rows: List[ApiEndpointAuthFileRemoveOutputAffectedRowDto] = Field(default_factory=list, description="List of affected rows during remove operation")

class ApiEndpointAuthFileRemoveSelectionDto(BoolType(ApiEndpointAuthFileRemoveOutputDto)):
    pass



# █████████████████████████████████████████████████████████████
# █ RECOVER DTO ███████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileRecoverDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.recover_metadesc

# ████ RECOVER INPUT DTO ██████████████████████████████████████


class ApiEndpointAuthFileRecoverInputWhereDto(PartialType(ApiEndpointAuthFileFindInputWhereDto)):
    pass

class ApiEndpointAuthFileRecoverInputDto(DtoModel):
    where: List[ApiEndpointAuthFileRecoverInputWhereDto] = Field(..., description="Where clause to apply recovery on specific records")


# ████ RECOVER OUTPUT DTO █████████████████████████████████████

class ApiEndpointAuthFileRecoverOutputAffectedRowDto(ApiEndpointAuthFileFindOutputRowDto):
    pass

class ApiEndpointAuthFileRecoverOutputDto(AffectedDto):
    affected_rows: List[ApiEndpointAuthFileRecoverOutputAffectedRowDto] = Field(default_factory=list, description="List of affected rows during recovery operation")

class ApiEndpointAuthFileRecoverSelectionDto(BoolType(ApiEndpointAuthFileRecoverOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ MARK AS MAIN DTO ██████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileMarkAsMainDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.mark_as_main_metadesc

# ████ MARK AS MAIN COMMON DTO ████████████████████████████████

@InputType
class MarkAsMainCommonInputDto(DtoModel):
    mark_as_main_field: ApiEndpointAuthFileMarkAsMainFieldEnum = Field(..., description="Please select the field to make as main.")

@ObjectType
class MarkAsMainCommonOutputDto(PartialType(MarkAsMainCommonInputDto)):
    pass
    

# ████ MARK AS MAIN INPUT DTO █████████████████████████████████
class ApiEndpointAuthFileMarkAsMainInputDto(IntersectionType(MarkAsMainInputDto, MarkAsMainCommonInputDto)):
    pass


# ████ MARK AS MAIN OUTPUT DTO ████████████████████████████████
class ApiEndpointAuthFileMarkAsMainOutputDto(IntersectionType(MarkAsMainOutputDto, MarkAsMainCommonOutputDto)):
    pass

class ApiEndpointAuthFileMarkAsMainSelectionDto(BoolType(ApiEndpointAuthFileMarkAsMainOutputDto)):
    pass



# █████████████████████████████████████████████████████████████
# █ RECORD POSITION DTO ███████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileRecordPositionDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.record_position_metadesc

# ████ RECORD POSITION INPUT DTO ██████████████████████████████

class ApiEndpointAuthFileRecordPositionInputDto(RecordPositionInputDto):
    pass

# ████ RECORD POSITION OUTPUT DTO █████████████████████████████

class ApiEndpointAuthFileRecordPositionOutputDto(RecordPositionOutputDto):
    pass

class ApiEndpointAuthFileRecordPositionSelectionDto(BoolType(ApiEndpointAuthFileRecordPositionOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ UPLOAD DTO ████████████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileUploadDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.upload_metadesc

# ████ UPLOAD REF TYPE DTO ████████████████████████████████████

class UploadFileFieldInputDto(DtoModel):
    file_field: ApiEndpointAuthFileUploadFileFieldEnum = Field(..., description="Please select the upload type.")

class UploadFileFieldOutputDto(PartialType(UploadFileFieldInputDto)):
    pass

# ███ UPLOAD INPUT DTO ████████████████████████████████████████

class ApiEndpointAuthFileUploadInputDto(IntersectionType(UploadInputDto, UploadFileFieldInputDto)):
    pass

# ███ UPLOAD OUTPUT DTO ███████████████████████████████████████

class ApiEndpointAuthFileUploadOutputDto(IntersectionType(UploadOutputDto, UploadFileFieldOutputDto)):
    pass

class ApiEndpointAuthFileUploadSelectionDto(BoolType(ApiEndpointAuthFileUploadOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ UPLOAD DELETE DTO █████████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileUploadDeleteDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.upload_delete_metadesc

# ███ UPLOAD DELETE INPUT DTO █████████████████████████████████

class ApiEndpointAuthFileUploadDeleteInputDto(IntersectionType(UploadFileFieldInputDto, UploadDeleteInputDto)):
    pass

# ███ UPLOAD DELETE OUTPUT DTO █████████████████████████████████

class ApiEndpointAuthFileUploadDeleteOutputDto(IntersectionType(UploadFileFieldOutputDto, UploadDeleteOutputDto)):
    pass

class ApiEndpointAuthFileUploadDeleteSelectionDto(BoolType(ApiEndpointAuthFileUploadDeleteOutputDto)):
    pass


# █████████████████████████████████████████████████████████████
# █ FILE RELOCATION DTO ███████████████████████████████████████
# █████████████████████████████████████████████████████████████

class ApiEndpointAuthFileFileRelocationDto(Dto):
    metaname: ClassVar[str] = None
    metadesc: ClassVar[str] = CrudMeta.file_relocation_metadesc

# ████ FILE RELOCATION INPUT DTO ██████████████████████████████

class ApiEndpointAuthFileFileRelocationInput(IntersectionType(FileRelocationInputDto, UploadFileFieldInputDto)):
    pass

# ████ FILE RELOCATION OUTPUT DTO █████████████████████████████

class ApiEndpointAuthFileFileRelocationOutput(IntersectionType(FileRelocationOutputDto, UploadFileFieldOutputDto)):
    pass

class ApiEndpointAuthFileFileRelocationSelectionDto(BoolType(ApiEndpointAuthFileFileRelocationOutput)):
    pass


