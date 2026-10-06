import time
from collections.abc import Callable
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt import PyJWKClient

from fea_core.auth import Auth0TokenVerifier
from fea_core.config import Settings
from fea_core.main import create_app

DOMAIN = "tenant.example.auth0.com"
AUDIENCE = "https://api.family-expense.test"
ISSUER = f"https://{DOMAIN}/"


class StubSigningKey:
    def __init__(self, key: Any) -> None:
        self.key = key


class StubJwkClient(PyJWKClient):
    def __init__(self, public_key: Any, error: Exception | None = None) -> None:
        self._public_key = public_key
        self._error = error

    def get_signing_key_from_jwt(self, token: str | bytes) -> Any:
        if self._error:
            raise self._error
        return StubSigningKey(self._public_key)


@pytest.fixture(scope="session")
def private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def make_token(private_key: rsa.RSAPrivateKey) -> Callable[..., str]:
    def _make(**overrides: Any) -> str:
        claims: dict[str, Any] = {
            "sub": "auth0|abc123",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": int(time.time()) + 300,
        }
        claims.update({k: v for k, v in overrides.items() if v is not None})
        for key in [k for k, v in overrides.items() if v is None]:
            claims.pop(key, None)
        return jwt.encode(claims, private_key, algorithm="RS256")

    return _make


@pytest.fixture
def settings() -> Settings:
    return Settings(auth0_domain=DOMAIN, auth0_audience=AUDIENCE)


@pytest.fixture
def build_client(
    settings: Settings, private_key: rsa.RSAPrivateKey
) -> Callable[[Exception | None], TestClient]:
    def _build(jwks_error: Exception | None = None) -> TestClient:
        verifier = Auth0TokenVerifier(
            ISSUER,
            AUDIENCE,
            settings.jwks_url,
            StubJwkClient(private_key.public_key(), error=jwks_error),
        )
        return TestClient(create_app(settings, verifier, configure_observability=False))

    return _build


@pytest.fixture
def client(build_client: Callable[[Exception | None], TestClient]) -> TestClient:
    return build_client(None)
