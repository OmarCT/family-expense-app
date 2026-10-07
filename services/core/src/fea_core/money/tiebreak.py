import hashlib
from collections.abc import Iterable

SEPARATOR = "\x1f"


def tiebreak_key(item_id: str, user_id: str) -> bytes:
    """Clave de desempate del largest remainder (ADR-0002).

    SHA-256 de `item_id`, U+001F y `user_id` en UTF-8. El separador evita que
    ("ab", "c") y ("a", "bc") produzcan la misma clave.
    """
    return hashlib.sha256(f"{item_id}{SEPARATOR}{user_id}".encode()).digest()


def order_by_tiebreak(item_id: str, user_ids: Iterable[str]) -> list[str]:
    """Participantes de menor a mayor clave: el primero recibe antes el centavo sobrante."""
    ordered = sorted(user_ids, key=lambda user_id: tiebreak_key(item_id, user_id))
    if len(set(ordered)) != len(ordered):
        raise ValueError("user_ids duplicados")
    return ordered
