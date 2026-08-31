from __future__ import annotations

from collections.abc import Callable
from typing import Any


Processor = Callable[[dict[str, Any]], dict[str, Any]]
_PROCESSORS: dict[str, Processor] = {}


class ProcessorRegistryError(RuntimeError):
    pass


def register_processor(key: str, processor: Processor) -> None:
    normalized = key.strip()
    if not normalized:
        raise ProcessorRegistryError("Processor key cannot be empty")
    _PROCESSORS[normalized] = processor


def get_processor(key: str) -> Processor:
    processor = _PROCESSORS.get(key.strip())
    if processor is None:
        raise ProcessorRegistryError(f"Unsupported processor_key: {key}")
    return processor


def list_processors() -> list[str]:
    return sorted(_PROCESSORS)
