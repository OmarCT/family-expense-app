"""Ejecuta testvectors/*.json contra la implementación Python (Slice 1).

Mientras no exista la implementación, el test se omite en lugar de pasar en falso.
"""
import json
from pathlib import Path

import pytest

VECTORS = Path(__file__).resolve().parents[3] / "testvectors"

pytestmark = pytest.mark.vectors


def _cases() -> list[dict]:  # type: ignore[type-arg]
    out: list[dict] = []  # type: ignore[type-arg]
    for f in sorted(VECTORS.glob("*.json")):
        data = json.loads(f.read_text())
        out.extend({"file": f.name, **c} for c in data["cases"])
    return out


@pytest.mark.parametrize("case", _cases(), ids=lambda c: f'{c["file"]}:{c["id"]}')
def test_vector(case: dict) -> None:  # type: ignore[type-arg]
    pytest.skip("Pendiente: implementar fea_core.money en Slice 1")
