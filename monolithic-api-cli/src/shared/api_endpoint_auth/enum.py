from enum import Enum

class ApiUserRoleEnum(int, Enum):
    APIUSER = 0
    APIADMIN = 1

class ApiEndpointAuthMarkAsMainFieldEnum(str, Enum):
    IS_MAIN = "is_main"

class ApiEndpointAuthUploadFileFieldEnum(str, Enum):
    PROFILE_PHOTO = "file_profile_photo"
    
