"""Ejecuta testvectors/*.json contra la implementación Python.

Las reglas sin implementación se omiten de forma explícita; las implementadas se ejecutan y un
vector incorrecto falla el build. Al implementar una regla, regístrala en HANDLERS.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from fea_core.money import order_by_tiebreak, tiebreak_key

VECTORS = Path(__file__).resolve().parents[3] / "testvectors"

pytestmark = pytest.mark.vectors


def _tiebreak_hash(case_input: dict[str, Any]) -> dict[str, Any]:
    return {"digest_hex": tiebreak_key(case_input["item_id"], case_input["user_id"]).hex()}


def _tiebreak_order(case_input: dict[str, Any]) -> dict[str, Any]:
    return {"order": order_by_tiebreak(case_input["item_id"], case_input["user_ids"])}


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "tiebreak_hash": _tiebreak_hash,
    "tiebreak_order": _tiebreak_order,
}


def _cases() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for f in sorted(VECTORS.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        out.extend({"file": f.name, "rule": data["rule"], **c} for c in data["cases"])
    return out


@pytest.mark.parametrize("case", _cases(), ids=lambda c: f"{c['file']}:{c['id']}")
def test_vector(case: dict[str, Any]) -> None:
    handler = HANDLERS.get(case["rule"])
    if handler is None:
        pytest.skip(f"Pendiente: regla {case['rule']} (Slice 1)")
    assert handler(case["input"]) == case["expected"]
