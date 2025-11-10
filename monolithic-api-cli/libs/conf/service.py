# libs/conf/conf_service.py
from typing import Any, Optional
from nest.core import Injectable

from libs.conf.setting import ConfSetting
from libs.conf.loader import ConfLoader
from functools import cached_property

from pathlib import Path
import os

@Injectable
class ConfService:
    def __init__(self) -> None:
        self._settings: ConfSetting = ConfLoader.load()
    
    """
    # cached property example in such case when its big config

    @cached_property
    @property
    def expensive(self) -> str:
        return compute_once()

    # use
    svc = ConfService(settings)
    print(svc.expensive)   # computed once, then cached
    del svc.expensive      # invalidate
    print(svc.expensive)   # recomputed
    """

    @property
    def root_path(self) -> str:
        # return the root project folder such as: /Users/core/Development/python/ai.thatsend.work_api
        # inside ai.thatsend.work_api entire project is stored, so main directory
        return Path.cwd() 

    @property
    def settings(self) -> ConfSetting:
        return self._settings

    # handy accessors
    @property
    def py_env(self) -> str:
        return self._settings.py_env or "default"
    
    @property
    def is_local_env(self) -> bool:
        return self.py_env == "local"
    
    @property
    def is_dev_env(self) -> bool:
        return self.py_env == "dev"
    
    @property
    def is_prod_env(self) -> bool:
        return self.py_env == "prod"

    @property
    def app_name(self) -> str:
        return self._settings.app_name
    
    @property
    def app_version(self) -> str:
        return self._settings.app_version
    
    @property
    def debug(self) -> bool:
        return self._settings.debug
    
    @property
    def debug_host(self) -> str:
        return self._settings.debug_host
    
    @property
    def debug_port(self) -> int:
        return self._settings.debug_port
    
    @property
    def tz(self) -> str:
        return self._settings.tz

    @property
    def project_name(self) -> str:
        return self._settings.project_name
    
    @property
    def app_host_domain(self) -> str:
        return self._settings.app_host_domain
    
    @property
    def app_host_cdn_domin(self) -> str:
        return self._settings.app_host_cdn_domin

    @property
    def app_host_web_domain(self) -> str:
        return self._settings.app_host_web_domain
    
    @property
    def app_host_backoffice_web_domain(self) -> str:
        return self._settings.app_host_backoffice_web_domain
    
    @property
    def app_local_web_domain(self) -> str:
        return self._settings.app_local_web_domain
    
    @property
    def app_local_web_port(self) -> int:
        return self._settings.app_local_web_port
    
    @property
    def app_local_backoffice_web_domain(self) -> str:
        return self._settings.app_local_backoffice_web_domain
    
    @property
    def app_local_backoffice_web_port(self) -> int:
        return self._settings.app_local_backoffice_web_port
    
    @property
    def app_listen_host(self) -> str:
        return self._settings.app_listen_host

    @property
    def gql_is_supergraph(self) -> bool:
        return self._settings.gql_is_supergraph
    
    @property
    def gql_disable_supergraph_playground(self) -> bool:
        return self._settings.gql_disable_supergraph_playground
    
    @property
    def gql_disable_subgraph_playground(self) -> bool:
        return self._settings.gql_disable_subgraph_playground
    
    @property
    def gql_disable_introspection(self) -> bool:
        return self._settings.gql_disable_introspection
    
    @property
    def gql_public_operations(self) -> list[str]:
        return self._settings.gql_public_operations

    @property
    def rest_public_routes(self) -> list[str]:
        return self._settings.rest_public_routes

    @property
    def gql_root_slug(self) -> str:
        return self._settings.gql_root_slug
    
    @property
    def gql_schema_dir(self) -> str:
        return self._settings.gql_schema_dir
    
    @property
    def gql_schema_dir_path(self) -> str:
        return Path(f"{self.root_path}/{self.gql_schema_dir}")
    
    @property
    def gql_complexity_limit(self) -> int:
        return self._settings.gql_complexity_limit
    
    @property
    def password_life_span_days(self) -> int:
        return self._settings.password_life_span_days
    
    @property
    def password_reset_warning_days(self) -> int:
        return self._settings.password_reset_warning_days
    
    @property
    def signin_otp_expire_minutes(self) -> int:
        return self._settings.signin_otp_expire_minutes
    
    @property
    def forgot_password_link_expire_hours(self) -> int:
        return self._settings.forgot_password_link_expire_hours
    
    @property
    def forgot_password_link_send_to_recovery_email(self) -> bool:
        return self._settings.forgot_password_link_send_to_recovery_email
    
    @property
    def max_file_size(self) -> int:
        return self._settings.max_file_size

    @property
    def max_files(self) -> int:
        return self._settings.max_files

    @property
    def one_byte_size(self) -> int:
        return self._settings.one_byte_size
    
    @property
    def log_dir(self) -> str:
        return self._settings.log_dir
    
    @property
    def log_dir_path(self) -> str:
        return Path(f"{self.root_path}/{self.log_dir}")
    
    @property
    def upload_dir(self) -> str:
        return self._settings.upload_dir
    
    @property
    def upload_dir_path(self) -> str:
        return Path(f"{self.root_path}/{self.upload_dir}")
    
    @property
    def tmp_dir(self) -> str:
        return self._settings.tmp_dir
    
    @property
    def tmp_dir_path(self) -> str:
        return Path(f"{self.root_path}/{self.tmp_dir}")
    
    @property
    def image_dir(self) -> str:
        return self._settings.image_dir
    
    @property
    def image_dir_path(self) -> str:
        return Path(f"{self.root_path}/{self.image_dir}")
    
    @property
    def cdn_url(self) -> str:
        return self._settings.cdn_url

    @property
    def common_secret(self) -> str:
        return self._settings.common_secret

    @property
    def common_salt(self) -> str:
        return self._settings.common_salt

    @property
    def common_iv(self) -> str:
        return self._settings.common_iv
    
    @property
    def cookie_secret(self) -> str:
        return self._settings.cookie_secret
    
    @property
    def session_secret(self) -> str:
        return self._settings.session_secret
    
    @property
    def session_salt(self) -> str:
        return self._settings.session_salt
    
    @property
    def session_iv(self) -> str:
        return self._settings.session_iv

    @property
    def mysql_host(self) -> str:
        return self._settings.mysql_host
    
    @property
    def mysql_port(self) -> int:
        return self._settings.mysql_port
    
    @property
    def mysql_user(self) -> str:
        return self._settings.mysql_user
    
    @property
    def mysql_pass(self) -> str:
        return self._settings.mysql_pass
    
    @property
    def mysql_dbname(self) -> str:
        return self._settings.mysql_dbname
    
    @property
    def mysql_logging(self) -> bool:
        return self._settings.mysql_logging
    
    @property
    def mysql_database_type(self) -> str:
        return self._settings.mysql_database_type
    
    @property
    def pgsql_host(self) -> str:
        return self._settings.pgsql_host
    
    @property
    def pgsql_port(self) -> int:
        return self._settings.pgsql_port
    
    @property
    def pgsql_user(self) -> str:
        return self._settings.pgsql_user
    
    @property
    def pgsql_pass(self) -> str:
        return self._settings.pgsql_pass
    
    @property
    def pgsql_dbname(self) -> str:
        return self._settings.pgsql_dbname
    
    @property
    def pgsql_logging(self) -> bool:
        return self._settings.pgsql_logging
    
    @property
    def pgsql_database_type(self) -> str:
        return self._settings.pgsql_database_type
    
    @property
    def pgsql_schema(self) -> str:
        return self._settings.pgsql_schema

    @property
    def sqlite_host(self) -> str:
        return self._settings.sqlite_host
    
    @property
    def sqlite_port(self) -> int:
        return self._settings.sqlite_port
    
    @property
    def sqlite_user(self) -> str:
        return self._settings.sqlite_user
    
    @property
    def sqlite_pass(self) -> str:
        return self._settings.sqlite_pass
    
    @property
    def sqlite_dbname(self) -> str:
        return self._settings.sqlite_dbname
    
    @property
    def sqlite_logging(self) -> bool:
        return self._settings.sqlite_logging
    
    @property
    def sqlite_database_type(self) -> str:
        return self._settings.sqlite_database_type
    
    @property
    def sqlite_source_dir(self) -> str:
        return self._settings.sqlite_source_dir
    
    @property
    def sqlite_source_path(self) -> str:
        return Path(f"{self.root_path}/{self.sqlite_source_dir}/{self.sqlite_dbname}")
    
    @property
    def redis_host(self) -> str:
        return self._settings.redis_host
    
    @property
    def redis_port(self) -> int:
        return self._settings.redis_port
    
    @property
    def redis_logging(self) -> bool:
        return self._settings.redis_logging
    
    @property
    def db_pool_size(self) -> int:
        return self._settings.db_pool_size
    
    @property
    def db_pool_max_overflow(self) -> int:
        return self._settings.db_pool_max_overflow
    
    @property
    def db_pool_per_ping(self) -> bool:
        return self._settings.db_pool_per_ping
    
    @property
    def db_pool_use_lifo(self) -> bool:
        return self._settings.db_pool_use_lifo
    
    @property
    def db_pool_echo(self) -> bool:
        return self._settings.db_pool_echo
    
    @property
    def db_pool_recycle(self) -> int:
        return self._settings.db_pool_recycle
    
    @property
    def better_sqlite3_data_source(self) -> str:
        return self._settings.better_sqlite3_data_source
    
    @property
    def better_sqlite3_data_source_path(self) -> str:
        return Path(f"{self.root_path}/{self.better_sqlite3_data_source}")
    @property
    def jwt_accesstoken_secret(self) -> str:
        return self._settings.jwt_accesstoken_secret
    
    @property
    def jwt_refreshtoken_secret(self) -> str:
        return self._settings.jwt_refreshtoken_secret
    
    @property
    def jwt_issuer(self) -> str:
        return self._settings.jwt_issuer
    
    @property
    def jwt_audience(self) -> str:
        return self._settings.jwt_audience
    
    @property
    def jwt_accesstoken_payload_name(self) -> str:
        return self._settings.jwt_accesstoken_payload_name
    
    @property
    def jwt_refreshtoken_payload_name(self) -> str:
        return self._settings.jwt_refreshtoken_payload_name
    
    @property
    def jwt_accesstoken_expires_in(self) -> str:
        return self._settings.jwt_accesstoken_expires_in
    
    @property
    def jwt_refreshtoken_expires_in(self) -> str:
        return self._settings.jwt_refreshtoken_expires_in

    @property
    def jwt_signing_alg_access(self) -> str:
        return self._settings.jwt_signing_alg_access
    
    @property
    def jwt_signing_alg_refresh(self) -> str:
        return self._settings.jwt_signing_alg_refresh
    
    @property
    def jwt_private_key_access_path(self) -> str:
        return self._settings.jwt_private_key_access_path
    
    @property
    def jwt_public_key_access_path(self) -> str:
        return self._settings.jwt_public_key_access_path
    
    @property
    def jwt_private_key_refresh_path(self) -> str:
        return self._settings.jwt_private_key_refresh_path
    
    @property
    def jwt_public_key_refresh_path(self) -> str:
        return self._settings.jwt_public_key_refresh_path
    
    @property
    def jwt_kid_access(self) -> str:
        return self._settings.jwt_kid_access
    
    @property
    def jwt_kid_refresh(self) -> str:
        return self._settings.jwt_kid_refresh
    
    @property
    def jwt_leeway(self) -> str:
        return self._settings.jwt_leeway
    
    @property
    def jwt_require_exp(self) -> bool:
        return self._settings.jwt_require_exp
    
    @property
    def jwt_require_iat(self) -> bool:
        return self._settings.jwt_require_iat
    
    @property
    def jwt_jwks_enabled(self) -> bool:
        return self._settings.jwt_jwks_enabled

    @property
    def jwt_jwks_cache_max_age(self) -> int:
        return self._settings.jwt_jwks_cache_max_age
    
    @property
    def smtp_service(self) -> Optional[str]:
        return self._settings.smtp_service
    
    @property
    def smtp_host(self) -> str:
        return self._settings.smtp_host
    
    @property
    def smtp_port(self) -> int:
        return self._settings.smtp_port

    @property
    def smtp_secure(self) -> bool:
        return self._settings.smtp_secure

    @property
    def smtp_user(self) -> str:
        return self._settings.smtp_user

    @property
    def smtp_pass(self) -> str:
        return self._settings.smtp_pass

    @property
    def smtp_from_email(self) -> str:
        return self._settings.smtp_from_email
    
    @property
    def format_date_time(self) -> str:
        return self._settings.format_date_time
    
    @property
    def format_date(self) -> str:
        return self._settings.format_date
    
    @property
    def format_time(self) -> str:
        return self._settings.format_time
    
    @property
    def num_of_records_per_page(self) -> int:
        return self._settings.num_of_records_per_page
    
    @property
    def img_thumb_width(self) -> int:
        return self._settings.img_thumb_width
    
    @property
    def img_thumb_height(self) -> int:
        return self._settings.img_thumb_height
    
    @property
    def img_thumb_file_extension(self) -> str:
        return self._settings.img_thumb_file_extension
    
    @property
    def entity_prefix(self) -> str:
        return self._settings.entity_prefix
    
    @property
    def masteruser_username(self) -> str:
        return self._settings.masteruser_username
    
    @property
    def masteruser_identify(self) -> str:
        return self._settings.masteruser_identify
    
    @property
    def enduser_username(self) -> str:
        return self._settings.enduser_username
    
    @property
    def enduser_identify(self) -> str:
        return self._settings.enduser_identify
    
    @property
    def enduser_role(self) -> str:
        return self._settings.enduser_role
    
    @property
    def log_console_level(self) -> str:
        return self._settings.log_console_level

    @property
    def log_console_foreign_min_level(self) -> str:
        return self._settings.log_console_foreign_min_level
    
    @property
    def log_to_files(self) -> bool:
        return self._settings.log_to_files
    
    @property
    def log_files_per_pid(self) -> bool:
        return self._settings.log_files_per_pid
    
    @property
    def log_keep_days(self) -> int:
        return self._settings.log_keep_days
    
    @property
    def log_sample_rate(self) -> float:
        return self._settings.log_sample_rate

    

    
    


    

    


    
