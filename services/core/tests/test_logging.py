from fea_core.logging_setup import REDACTED, redact_pii


def test_pii_keys_are_redacted() -> None:
    event = {
        "event": "login",
        "email": "ana@example.com",
        "name": "Ana",
        "authorization": "Bearer abc",
        "sub": "auth0|abc",
        "user_id": "9c1d",
    }
    out = redact_pii(None, "info", dict(event))
    for key in ("email", "name", "authorization", "sub"):
        assert out[key] == REDACTED
    assert out["user_id"] == "9c1d"
    assert "ana@example.com" not in str(out)
