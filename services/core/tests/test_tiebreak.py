import pytest
from hypothesis import given
from hypothesis import strategies as st

from fea_core.money import order_by_tiebreak, tiebreak_key

ids = st.text(min_size=1, max_size=40)


def test_separator_prevents_concatenation_collisions() -> None:
    assert tiebreak_key("ab", "c") != tiebreak_key("a", "bc")


def test_key_is_a_32_byte_digest() -> None:
    assert len(tiebreak_key("item", "user")) == 32


def test_duplicate_users_are_rejected() -> None:
    with pytest.raises(ValueError):
        order_by_tiebreak("item", ["u1", "u1"])


@given(item=ids, users=st.lists(ids, min_size=1, max_size=8, unique=True), seed=st.randoms())
def test_order_does_not_depend_on_input_order(item: str, users: list[str], seed: object) -> None:
    shuffled = list(users)
    seed.shuffle(shuffled)  # type: ignore[attr-defined]
    assert order_by_tiebreak(item, users) == order_by_tiebreak(item, shuffled)


@given(item=ids, users=st.lists(ids, min_size=1, max_size=8, unique=True))
def test_order_is_a_permutation_of_the_participants(item: str, users: list[str]) -> None:
    assert sorted(order_by_tiebreak(item, users)) == sorted(users)
