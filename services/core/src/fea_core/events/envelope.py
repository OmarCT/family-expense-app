from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class EventEnvelope(BaseModel):
    """Sobre común de todo evento del outbox.

    La secuencia por hogar no forma parte del sobre del productor: se asigna al confirmar
    (ADR-0006). `participant_ids=None` significa visible para todo el hogar; una lista
    restringe el evento a esos usuarios (capa 1 de visibilidad).
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    event_id: UUID
    event_type: str = Field(min_length=1)
    schema_version: int = Field(ge=1)
    occurred_at: AwareDatetime
    household_id: UUID
    correlation_id: str = Field(min_length=1)
    actor_id: UUID | None = None
    participant_ids: tuple[UUID, ...] | None = None
    payload: dict[str, Any]

    def with_payload(self, payload: dict[str, Any], schema_version: int) -> "EventEnvelope":
        return self.model_copy(update={"payload": payload, "schema_version": schema_version})
