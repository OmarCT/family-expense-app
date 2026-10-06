from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, ConfigDict


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject: str

    @property
    def user_id(self) -> UUID:
        return uuid5(NAMESPACE_URL, f"fea:user:{self.subject}")


class InvalidTokenError(Exception):
    pass


class AuthUnavailableError(Exception):
    pass


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Principal: ...


class Auth0TokenVerifier:
    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_url: str,
        jwk_client: PyJWKClient | None = None,
    ) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks = jwk_client or PyJWKClient(jwks_url, cache_keys=True)

    def verify(self, token: str) -> Principal:
        try:
            key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.PyJWKClientConnectionError as exc:
            raise AuthUnavailableError from exc
        except jwt.PyJWTError as exc:
            raise InvalidTokenError from exc
        return Principal(subject=str(claims["sub"]))
