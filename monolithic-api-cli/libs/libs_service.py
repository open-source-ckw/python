"""Python port of the NestJS ``LibraryAppService`` utilities."""

from __future__ import annotations

import base64
import mimetypes
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions
from nest.core import Injectable
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.inspection import inspect as sa_inspect

from libs.conf.service import ConfService
from libs.crud.dto.snapshot_dto import SnapshotListDto
from libs.libs_protocol import FileMetadata
from libs.log.service import LogService


@Injectable
class LibsService:
    """Collection of stateless helpers shared across CRUD engines."""

    _password_hasher = PasswordHasher(time_cost=3, memory_cost=4096, parallelism=1)

    def __init__(self, conf_service: ConfService, log_service: LogService) -> None:
        self.conf_service = conf_service
        self.log_service = log_service.bind(service=self.__class__.__name__)

    # ------------------------------------------------------------------
    # Base64 helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _xor_bytes_with_secret(data: bytes) -> bytes:
        """Internal: XOR data with module-level SECRET_KEY (wraps if key shorter)."""
        _SECRET_KEY = b"A7eT0)" # secret key to encrypt
        if not _SECRET_KEY:
            return data
        klen = len(_SECRET_KEY)
        return bytes(b ^ _SECRET_KEY[i % klen] for i, b in enumerate(data))

    @staticmethod
    def base64_enc(value: str | int | bytes) -> str:
        """"
        Encode value (str|int|bytes) to Base64 after XOR-obfuscating with SECRET_KEY.
        Usage: set SECRET_KEY (bytes) above this function.
        """
        if isinstance(value, bytes):
            payload = value
        else:
            payload = str(value).encode("utf-8")
        obf = LibsService._xor_bytes_with_secret(payload)
        return base64.b64encode(obf).decode("ascii")

    @staticmethod
    def base64_dec(encoded_value: str | bytes) -> str:
        """
        Decode Base64 produced by base64_enc and reverse XOR with SECRET_KEY.
        Returns decoded UTF-8 string.
        """
        encoded_bytes = encoded_value if isinstance(encoded_value, bytes) else encoded_value.encode("ascii")
        decoded = base64.b64decode(encoded_bytes)
        deobf = LibsService._xor_bytes_with_secret(decoded)
        return deobf.decode("utf-8")

    # ------------------------------------------------------------------
    # Hashing helpers
    # ------------------------------------------------------------------
    @classmethod
    def get_hash(cls, value: str) -> str:
        """[/]Return a Base64 encoded Argon2 hash for the provided value."""

        if not value:
            raise ValueError("String not found for hashing.")

        try:
            hashed = cls._password_hasher.hash(value)
        except Exception as exc:  # pragma: no cover - library failure path
            raise ValueError(
                f"Error hashing your string. Verify your string and try again. {exc}"
            ) from exc

        return cls.base64_enc(hashed)

    @classmethod
    def match_hash(cls, encoded_hash: str, candidate: str) -> bool:
        """[/]Verify the candidate string against a Base64 encoded hash."""

        if not encoded_hash:
            return False

        try:
            stored_hash = cls.base64_dec(encoded_hash)
            return cls._password_hasher.verify(stored_hash, candidate)
        except (argon2_exceptions.VerifyMismatchError, ValueError):
            return False
        except argon2_exceptions.VerificationError:
            return False
        except Exception:  # pragma: no cover - unexpected decoder errors
            return False

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------
    def format_bytes(self, size_in_bytes: int) -> str:
        """[/]Format a byte-size using the configured ``one_byte_size`` base."""

        byte = self.conf_service.one_byte_size
        megabytes = size_in_bytes / (byte * byte)
        if megabytes >= byte:
            gigabytes = megabytes / byte
            return f"{gigabytes:.2f} GB"
        return f"{megabytes:.2f} MB"

    @staticmethod
    def format_time(seconds: int) -> str:
        """[/]Convert *seconds* into a human readable time span."""

        minute = 60
        hour = 60 * minute
        day = 24 * hour
        year = int(365.25 * day)
        month = year / 12

        if seconds >= year:
            years = seconds // year
            months = int((seconds % year) // month)
            return f"{years} years" + (f", {months} months" if months else "")
        if seconds >= month:
            months = int(seconds // month)
            days = int((seconds % month) // day)
            return f"{months} months" + (f", {days} days" if days else "")
        if seconds >= day:
            days = seconds // day
            hours = (seconds % day) // hour
            return f"{days} days" + (f", {hours} hours" if hours else "")
        if seconds >= hour:
            hours = seconds // hour
            minutes = (seconds % hour) // minute
            return f"{hours} hours" + (f", {minutes} minutes" if minutes else "")
        if seconds >= minute:
            minutes = seconds // minute
            remaining_seconds = seconds % minute
            return f"{minutes} minutes" + (
                f", {remaining_seconds} seconds" if remaining_seconds else ""
            )
        return f"{seconds} seconds"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """[/]Mask an email by replacing local-part characters with asterisks."""

        if "@" not in email:
            return email
        name, domain = email.split("@", 1)
        if not name:
            return email
        if len(name) == 1:
            masked_name = name
        else:
            masked_name = name[0] + "*" * (len(name) - 1)
        return f"{masked_name}@{domain}"

    @staticmethod
    def mask_mobile_number(mobile_number: str) -> str:
        """[/]Mask all but the first two and last three digits of a phone number."""

        if len(mobile_number) <= 5:
            return mobile_number
        return f"{mobile_number[:2]}{'*' * (len(mobile_number) - 5)}{mobile_number[-3:]}"

    # ------------------------------------------------------------------
    # File metadata helpers
    # ------------------------------------------------------------------
    @staticmethod
    def get_file_metadata(file_path: str | Path) -> FileMetadata:
        """[/]Return metadata for the file located at *file_path*."""

        path = Path(file_path)
        stats = path.stat()
        mime_type, encoding_guess = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/octet-stream"
        charset = "utf-8" if mime_type.startswith("text/") else "binary"
        if encoding_guess in {"utf-8", "utf8", "latin-1", "ascii"}:
            charset = encoding_guess

        return FileMetadata(
            filename=path.name,
            name=path.stem,
            extension=path.suffix,
            size=stats.st_size,
            created=datetime.fromtimestamp(stats.st_ctime),
            modified=datetime.fromtimestamp(stats.st_mtime),
            mimetype=mime_type,
            encoding=charset,
        )
    
    @staticmethod
    def merge_snapshot(
        current_snap: SnapshotListDto, new_snap: SnapshotListDto
    ) -> SnapshotListDto:
        """Merge the snapshot buckets from ``new_snap`` into ``current_snap``."""

        fields = type(current_snap).model_fields
        updates = {}
        for name in fields:
            cur = getattr(current_snap, name, None)
            nxt = getattr(new_snap, name, None)
            if isinstance(cur, list) and isinstance(nxt, list):
                updates[name] = [*cur, *nxt]
        return current_snap.model_copy(update=updates)
    
    @staticmethod
    def _normalise_mapping(value: Any) -> Dict[str, Any]:
        from pydantic import BaseModel

        if isinstance(value, Mapping):
            return dict(value)
        if isinstance(value, BaseModel):  # type: ignore[isinstance]
            return value.model_dump(exclude_unset=True)
        if hasattr(value, "model_dump"):
            data = value.model_dump(exclude_unset=True)
            if isinstance(data, Mapping):
                return dict(data)
        if hasattr(value, "__dict__"):
            items: Dict[str, Any] = {}
            for key in dir(value):
                if key.startswith("_"):
                    continue
                if not hasattr(value, key):
                    continue
                attr = getattr(value, key)
                if callable(attr):
                    continue
                items[key] = attr
            return items
        return {}

    @classmethod
    def filter_input_as_reference(
        cls, input_data: Any, reference: Any
    ) -> Dict[str, Any]:
        """
        Filter *input_data* to keys that exist within *reference*.
        A method to filter keys from an object based on another object.
        Returns a new object with only the keys present in the reference object.
        
        @param {any} reference - The object to filter keys with.
        @return {Promise<Partial<T>>} A new object with only the keys present in the reference object.
        */
        """

        input_mapping = cls._normalise_mapping(input_data)
        if not input_mapping:
            raise ValueError("Input data must be a mapping.")
        reference_mapping = cls._normalise_mapping(reference)
        reference_keys = set(reference_mapping.keys())
        return {key: value for key, value in input_mapping.items() if key in reference_keys}

    # ------------------------------------------------------------------
    # ORM helpers
    # ------------------------------------------------------------------
    @staticmethod
    def entity_fields_arr(entity: Any) -> List[str]:
        """
        Return a list of mapped column names for the given SQLModel entity.
        Retrieves an array of entity field names from the given repository.
        """

        try:
            mapper = sa_inspect(entity)
        except NoInspectionAvailable:
            if isinstance(entity, Iterable):
                names: List[str] = []
                for column in entity:
                    for attr in ("key", "name", "property_name", "propertyName"):
                        value = getattr(column, attr, None)
                        if value:
                            names.append(value)
                            break
                return names
            return []

        return [column.key for column in mapper.column_attrs]  # type: ignore[attr-defined]

    
