from collections.abc import Callable
from typing import Any

from fea_core.events.envelope import EventEnvelope

Payload = dict[str, Any]
Upcaster = Callable[[Payload], Payload]


class EventSchemaError(Exception):
    """El consumidor no puede interpretar el evento: debe detenerse y alertar, nunca saltarlo."""


class UnknownEventTypeError(EventSchemaError):
    pass


class UnknownSchemaVersionError(EventSchemaError):
    pass


class UpcasterRegistry:
    """Versión vigente por tipo de evento y upcasters para cambios que rompen compatibilidad.

    Los cambios aditivos no necesitan upcaster ni subir la versión. Un upcaster `n -> n + 1`
    devuelve un payload nuevo; el evento almacenado nunca se modifica.
    """

    def __init__(self) -> None:
        self._latest: dict[str, int] = {}
        self._upcasters: dict[tuple[str, int], Upcaster] = {}

    def register_type(self, event_type: str, latest_version: int = 1) -> None:
        if latest_version < 1:
            raise ValueError("latest_version debe ser >= 1")
        self._latest[event_type] = latest_version

    def register_upcaster(self, event_type: str, from_version: int, upcaster: Upcaster) -> None:
        self._upcasters[(event_type, from_version)] = upcaster
        self._latest[event_type] = max(self._latest.get(event_type, 1), from_version + 1)

    def upcast_to_latest(self, event: EventEnvelope) -> EventEnvelope:
        latest = self._latest.get(event.event_type)
        if latest is None:
            raise UnknownEventTypeError(f"tipo de evento no registrado: {event.event_type}")
        if event.schema_version > latest:
            raise UnknownSchemaVersionError(
                f"{event.event_type} v{event.schema_version} es posterior a la v{latest} conocida"
            )
        current = event
        while current.schema_version < latest:
            upcaster = self._upcasters.get((current.event_type, current.schema_version))
            if upcaster is None:
                raise UnknownSchemaVersionError(
                    f"sin upcaster para {current.event_type} v{current.schema_version}"
                )
            current = current.with_payload(
                upcaster(dict(current.payload)), current.schema_version + 1
            )
        return current
