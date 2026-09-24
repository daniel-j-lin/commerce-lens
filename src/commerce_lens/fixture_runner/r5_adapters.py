"""Code-owned allowlist for independent deterministic subjects under test."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from commerce_lens.fixture_runner.r5_manifest import ActualProjection, ExecutionMode, LoadedR5Fixture


AdapterProducer = Callable[[LoadedR5Fixture], ActualProjection]
_ADAPTER_ID = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


class AdapterRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class AdapterRegistration:
    adapter_id: str
    execution_mode: ExecutionMode
    capability_name: str
    capability_version: str
    actual_output_producer: str
    producer: AdapterProducer | None

    def __post_init__(self) -> None:
        if _ADAPTER_ID.fullmatch(self.adapter_id) is None:
            raise AdapterRegistryError("adapter ID is invalid")
        if not self.capability_name or not self.capability_version or not self.actual_output_producer:
            raise AdapterRegistryError("adapter capability and actual-output producer must be explicit")
        if self.execution_mode is ExecutionMode.DEPENDENCY_GATE and self.producer is not None:
            raise AdapterRegistryError("dependency_gate adapter cannot fabricate an actual-output producer result")

    @property
    def available(self) -> bool:
        return self.producer is not None


class AdapterRegistry:
    """Registry mechanics only; PF0 registers no CommerceLens semantic adapter."""

    def __init__(self) -> None:
        self._entries: dict[str, AdapterRegistration] = {}

    def register(self, registration: AdapterRegistration) -> None:
        if registration.adapter_id in self._entries:
            raise AdapterRegistryError(f"duplicate adapter ID: {registration.adapter_id}")
        self._entries[registration.adapter_id] = registration

    def require(self, adapter_id: str) -> AdapterRegistration:
        try:
            return self._entries[adapter_id]
        except KeyError as exc:
            raise AdapterRegistryError(f"unknown adapter ID: {adapter_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))
