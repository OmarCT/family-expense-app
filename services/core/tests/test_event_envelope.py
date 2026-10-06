from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from fea_core.events import (
    EventEnvelope,
    UnknownEventTypeError,
    UnknownSchemaVersionError,
    UpcasterRegistry,
)


def make_event(version: int = 1, payload: dict[str, Any] | None = None) -> EventEnvelope:
    return EventEnvelope(
        event_id=uuid4(),
        event_type="expense.created",
        schema_version=version,
        occurred_at=datetime(2026, 10, 6, tzinfo=UTC),
        household_id=uuid4(),
        correlation_id="corr-1",
        payload=payload if payload is not None else {"total_centavos": 1000},
    )


def test_roundtrip_through_json() -> None:
    event = make_event()
    assert EventEnvelope.model_validate_json(event.model_dump_json()) == event


def test_requires_schema_version_and_positive() -> None:
    data = make_event().model_dump(mode="json")
    del data["schema_version"]
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate(data)
    data["schema_version"] = 0
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate(data)


def test_rejects_naive_datetime() -> None:
    data = make_event().model_dump(mode="json")
    data["occurred_at"] = "2026-10-06T00:00:00"
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate(data)


def test_additive_fields_are_ignored() -> None:
    data = make_event().model_dump(mode="json")
    data["new_envelope_field"] = "added later"
    assert EventEnvelope.model_validate(data).event_type == "expense.created"


def test_current_version_passes_through_unchanged() -> None:
    registry = UpcasterRegistry()
    registry.register_type("expense.created", 1)
    event = make_event()
    assert registry.upcast_to_latest(event) == event


def test_unknown_future_version_stops_consumer() -> None:
    registry = UpcasterRegistry()
    registry.register_type("expense.created", 2)
    with pytest.raises(UnknownSchemaVersionError):
        registry.upcast_to_latest(make_event(version=3))


def test_unregistered_event_type_stops_consumer() -> None:
    with pytest.raises(UnknownEventTypeError):
        UpcasterRegistry().upcast_to_latest(make_event())


def test_missing_upcaster_in_chain_stops_consumer() -> None:
    registry = UpcasterRegistry()
    registry.register_type("expense.created", 3)
    registry.register_upcaster("expense.created", 2, lambda p: p)
    with pytest.raises(UnknownSchemaVersionError):
        registry.upcast_to_latest(make_event(version=1))


def test_upcast_chain_does_not_mutate_stored_event() -> None:
    registry = UpcasterRegistry()
    registry.register_upcaster("expense.created", 1, lambda p: {**p, "currency": "MXN"})
    registry.register_upcaster(
        "expense.created",
        2,
        lambda p: {"total": {"centavos": p["total_centavos"], "currency": p["currency"]}},
    )
    stored = make_event(version=1, payload={"total_centavos": 1500})
    upgraded = registry.upcast_to_latest(stored)
    assert upgraded.schema_version == 3
    assert upgraded.payload == {"total": {"centavos": 1500, "currency": "MXN"}}
    assert stored.schema_version == 1
    assert stored.payload == {"total_centavos": 1500}


@given(centavos=st.integers(min_value=0, max_value=10**12))
def test_upcast_preserves_integer_centavos(centavos: int) -> None:
    registry = UpcasterRegistry()
    registry.register_upcaster(
        "expense.created", 1, lambda p: {"total": {"centavos": p["total_centavos"]}}
    )
    upgraded = registry.upcast_to_latest(make_event(payload={"total_centavos": centavos}))
    assert upgraded.payload["total"]["centavos"] == centavos
    assert isinstance(upgraded.payload["total"]["centavos"], int)
