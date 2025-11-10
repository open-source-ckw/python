"""Utility typing constructs shared across library helpers.

This module replaces the TypeScript mapped-type helpers with
runtime-checkable protocols that describe dictionary-like objects.
It also exposes the :class:`FileMetadata` dataclass used by
``LibsService`` and the upload engines.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, MutableMapping, Protocol, TypeVar, runtime_checkable


KT = TypeVar("KT", bound=str)
VT = TypeVar("VT")


@runtime_checkable
class KeyReadableMapping(Protocol[KT, VT]):
    """Protocol for objects that expose ``keys``/``__getitem__`` access."""

    def keys(self) -> Iterable[KT]:
        ...

    def __getitem__(self, key: KT) -> VT:
        ...


@runtime_checkable
class MutableKeyMapping(KeyReadableMapping[KT, VT], Protocol[KT, VT]):
    """Mutable variant used when updates are required."""

    def __setitem__(self, key: KT, value: VT) -> None:
        ...

    def __delitem__(self, key: KT) -> None:
        ...


#: Alias mirroring ``MakeRequiredType`` from TypeScript.
MakeRequiredType = MutableMapping[str, VT]

#: Alias mirroring ``MakeOptionalType`` from TypeScript.
MakeOptionalType = MutableMapping[str, VT | None]

#: Alias mirroring ``MakeAnyType`` from TypeScript.
MakeAnyType = MutableMapping[str, Any]


@dataclass(slots=True)
class FileMetadata:
    """Filesystem metadata for an uploaded or generated asset."""

    filename: str
    name: str
    extension: str
    size: int
    created: datetime
    modified: datetime
    mimetype: str
    encoding: str


__all__ = [
    "FileMetadata",
    "KeyReadableMapping",
    "MakeAnyType",
    "MakeOptionalType",
    "MakeRequiredType",
    "MutableKeyMapping",
]
