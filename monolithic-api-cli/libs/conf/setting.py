# libs/conf/conf_settings.py
from typing import Optional
from pydantic import AnyUrl, BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class ConfSetting(BaseSettings):

    model_config = SettingsConfigDict(
            env_nested_delimiter="__",   # GROUPA__URL -> groupa.url etc.
            case_sensitive=False,
            extra="ignore",
    )

    # PRIVATE OR DYNAMIC vars (not in env only availabe here)
    private_flag_x: bool = False # not accessible as getter is not created in conf_service.py
    root_path: str = ""
    debug_host: str = "127.0.0.1"
    debug_port: int = 5678
    log_dir_path: str = ""
    upload_dir_path: str = ""
    tmp_dir_path: str = ""
    image_dir_path: str = ""
    sqlite_source_path: str = ""
    better_sqlite3_data_source_path: str = ""
    rest_public_routes: list[str] = ["/rest/health", "/rest/mint-test-jwt", "/rest/hello", "/rest/login", "/rest/reset-password", "/rest/refresh-jwt"]  # paths under FastAPI that should stay accessible without JWT
    gql_public_operations: list[str] = ["IntrospectionQuery", "GraphHealth", "GraphMintTestJwt", 'GraphHello', "GraphLogin", "GraphResetPassword", "GraphRefreshJWT", "GraphSignup"] #  IntrospectionQuery is operation performaed by apollo to get schema, it also send jwt but we skipped as there are too many requests and constant request consume memory so bypass
    gql_schema_dir_path: str = ""

    class GroupaSetting(BaseModel):
        url: str | None = None
        pool_size: int = 10
        password: Optional[SecretStr] = None

    class GroupbSetting(BaseModel):
        url: str | None = None
        enabled: bool = True

    # Grouped configs vars
    groupa: GroupaSetting
    groupb: GroupbSetting

    """
    App metadata and defaults if we need
    consider to add important configs here in such case missing in any env or config file
    default blue print for each env var
    """
    # 👇 dynamic: no Literal[...] — accept any string from env
    py_env: Optional[str] = Field(default=None, alias="PY_ENV")

    app_name: str = "all-in-one-python-framework"
    app_version: str = "0.1.0"
    debug: bool = False

    tz: str = "UTC"
    project_name: str = "All in one Python app"

    # --- App host and routing ---
    app_host_domain: str = "http://localhost:20061"
    app_host_cdn_domin: str = "http://localhost:20080"
    app_host_web_domain: str = "http://localhost:20080"
    app_host_backoffice_web_domain: str = "http://localhost:20079"
    
    app_local_web_domain: str = "localhost"
    app_local_web_port: int = 20080
    app_local_backoffice_web_domain: str = "localhost"
    app_local_backoffice_web_port: int = 20079
    app_listen_host: str = "localhost"

    # --- Feature flags / GraphQL ---
    gql_is_supergraph: bool = False
    gql_disable_supergraph_playground: bool = False
    gql_disable_subgraph_playground: bool = False
    gql_disable_introspection: bool = True 
    gql_root_slug: str = "graphql"
    gql_schema_dir: str = "/graphql/schema"
    gql_complexity_limit: int = 0

    # --- Security / Auth policy ---
    password_life_span_days: int = 365
    password_reset_warning_days: int = 180
    signin_otp_expire_minutes: int = 10
    forgot_password_link_expire_hours: int = 2
    forgot_password_link_send_to_recovery_email: bool = True
    
    # --- Static storage specification ---
    one_byte_size: int = 1024
    max_file_size: int = 20 * 1024 * 1024  # 20971520
    max_files: int = 10
    log_dir: str = "/log"
    upload_dir: str = "/assets/upload"
    tmp_dir: str = "/assets/tmp"
    image_dir: str = "/assets/image"
    cdn_url: str = "/cdn"
    
    # --- Common secret, salt and iv ---
    common_secret: str = ("AD2A9F143EB457C72059F5097E9BA07E41EB0F2F8B7CF2734283655BFA9FDD73")
    common_salt: str = "37A6C7AFA29CAB98"
    common_iv: str = "74D5350D1A4A49374FF38661F1064A9A"
    
    # --- Stateful data storage ---
    cookie_secret: str = ("7CDFE783DB8386303EF0989E575DBC9D75597B085325435E5B6B77540EB8F355")
    session_secret: str = ("FCEC7E5412EF1A3CD267432A7231210658EE83BE591B424A5433D28F3897C53C")
    session_salt: str = "2BABDD16DF09FB00"
    session_iv: str = "47158B020333E996FD43B8FE7C1A5634"
    
    # --- Database ---
    mysql_host: str = "localhost"
    mysql_port: int = 0000
    mysql_user: str = "root"
    mysql_pass: str = "root"
    mysql_dbname: str = "enterprise_application_db"
    mysql_logging: bool = False
    mysql_database_type: str = "mysql"

    pgsql_host: str = "localhost"
    pgsql_port: int = 0000
    pgsql_user: str = "root"
    pgsql_pass: str = "root"
    pgsql_dbname: str = "enterprise_application_db"
    pgsql_logging: bool = False
    pgsql_database_type: str = "pgsql"
    pgsql_schema: str = "public"

    sqlite_host: str | None = None 
    sqlite_port: int | None = None
    sqlite_user: str = "root"
    sqlite_pass: str = "root"
    sqlite_dbname: str = "sqlite.db"
    sqlite_logging: bool = False
    sqlite_database_type: str = "sqlite"
    sqlite_source_dir: str = "/data-source"
    
    redis_host: str = "localhost"
    redis_port: int = 0
    redis_logging: bool = False

    db_pool_size: int = 10
    db_pool_max_overflow: int = 10
    db_pool_per_ping: bool = True
    db_pool_use_lifo: bool = True
    db_pool_echo: bool = False
    db_pool_recycle: int = 3600

    better_sqlite3_data_source: str = "/data-source/sqlite3.db"
    
    # --- JWT ---
    jwt_accesstoken_secret: str = ("CD9995FB4B72CB0A20614F0F85DC29D4C47B9B987F7A0FB9FD88FE52811C6D8C")
    jwt_refreshtoken_secret: str = ("3A237D96597B05C27C30F1E805DC258E7AD688BBEA4E1A52086DF4912FF9C919")
    jwt_issuer: str = "THATSEND"
    jwt_audience: str = "Application"
    jwt_accesstoken_payload_name: str = "access_token"
    jwt_refreshtoken_payload_name: str = "refresh_token"
    jwt_accesstoken_expires_in: str = "1d"
    jwt_refreshtoken_expires_in: str = "7d"

    jwt_signing_alg_access: str = "RS256"
    jwt_signing_alg_refresh: str = "RS256"
    jwt_private_key_access_path: str = ""
    jwt_public_key_access_path: str = ""
    jwt_private_key_refresh_path: str = ""
    jwt_public_key_refresh_path: str = ""
    jwt_kid_access: str = ""
    jwt_kid_refresh: str = ""
    jwt_leeway: str = "30s"
    jwt_require_exp: bool = True
    jwt_require_iat: bool = True
    jwt_jwks_enabled: bool = False
    jwt_jwks_cache_max_age: int = 3600
    
    # --- SMTP ---
    smtp_service: Optional[str] = None
    smtp_host: str = "mail.thatsend.com"
    smtp_port: int = 465
    smtp_secure: bool = True
    smtp_user: str = "testsmtp@thatsend.com"
    smtp_pass: str = "P*7HThMB@P*b"
    smtp_from_email: str = "localrealestate@gmail.com"
    
    # --- Data formats ---
    format_date_time: str = "d MMM yyyy hh:mm:ss aaa"
    format_date: str = "d MMM yyyy"
    format_time: str = "hh:mm:ss aaa"
    
    # --- Pagination ---
    num_of_records_per_page: int = 25
    
    # --- Image processing ---
    img_thumb_width: int = 200
    img_thumb_height: int = 150
    img_thumb_file_extension: str = ".jpeg"
    
    # --- Database entity ---
    entity_prefix: str = "te_"
    
    # --- Users ---
    masteruser_username: str = "admin"
    masteruser_identify: str = "opwq@AK56"
    enduser_username: str = "enduser@domain.local"
    enduser_identify: str = "opwq@AK56"
    enduser_role: str = "USER"

    log_console_level: str = "TRACE"
    log_console_foreign_min_level: str = "ERROR"
    log_to_files: bool = False
    log_files_per_pid: bool = False
    log_keep_days: int = 14
    log_sample_rate: float = 1.0
    