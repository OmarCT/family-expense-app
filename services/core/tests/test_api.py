from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import jwt
import yaml
from fastapi.testclient import TestClient

from fea_core.config import Settings
from fea_core.main import create_app

CONTRACT = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_needs_no_token(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_returns_stable_user_id_and_locale(
    client: TestClient, make_token: Callable[..., str]
) -> None:
    first = client.get("/v1/me", headers=bearer(make_token()))
    second = client.get("/v1/me", headers=bearer(make_token()))
    assert first.status_code == 200
    assert UUID(first.json()["id"])
    assert first.json() == second.json()
    assert first.json()["locale"] == "es-MX"


def test_me_without_token_uses_the_single_error_format(client: TestClient) -> None:
    response = client.get("/v1/me")
    body = response.json()
    assert response.status_code == 401
    assert body["code"] == "unauthorized"
    assert body["message"] == "Necesitas iniciar sesión."
    assert UUID(body["correlation_id"])
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_rejects_wrong_audience_issuer_expired_and_missing_claims(
    client: TestClient, make_token: Callable[..., str]
) -> None:
    bad_tokens = [
        make_token(aud="https://otra.api"),
        make_token(iss="https://evil.example/"),
        make_token(exp=1),
        make_token(sub=None),
        "no-es-un-jwt",
    ]
    for token in bad_tokens:
        assert client.get("/v1/me", headers=bearer(token)).status_code == 401


def test_unknown_route_uses_the_error_format(client: TestClient) -> None:
    response = client.get("/v1/no-existe")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_correlation_id_is_echoed_or_replaced(client: TestClient) -> None:
    given = "6f1c1d0e-5b8a-4c8e-9a52-0d3a9d3c2b11"
    echoed = client.get("/v1/health", headers={"X-Correlation-Id": given})
    assert echoed.headers["X-Correlation-Id"] == given
    replaced = client.get("/v1/health", headers={"X-Correlation-Id": "no-uuid"})
    assert UUID(replaced.headers["X-Correlation-Id"])
    assert replaced.headers["X-Correlation-Id"] != "no-uuid"


def test_error_carries_the_request_correlation_id(client: TestClient) -> None:
    given = "6f1c1d0e-5b8a-4c8e-9a52-0d3a9d3c2b11"
    response = client.get("/v1/me", headers={"X-Correlation-Id": given})
    assert response.json()["correlation_id"] == given


def test_jwks_outage_is_503_not_401(
    build_client: Callable[[Exception | None], TestClient], make_token: Callable[..., str]
) -> None:
    client = build_client(jwt.PyJWKClientConnectionError("down"))
    response = client.get("/v1/me", headers=bearer(make_token()))
    assert response.status_code == 503
    assert response.json()["code"] == "auth_unavailable"


def test_app_matches_the_openapi_contract(client: TestClient) -> None:
    contract = yaml.safe_load(CONTRACT.read_text())
    expected = {
        (path, method, op["operationId"])
        for path, item in contract["paths"].items()
        for method, op in item.items()
    }
    served = client.app.openapi()  # type: ignore[attr-defined]
    actual = {
        (path.removeprefix("/v1"), method, op["operationId"])
        for path, item in served["paths"].items()
        for method, op in item.items()
    }
    assert actual == expected


def test_spans_carry_correlation_id_and_no_personal_data(
    settings: Settings, make_token: Callable[..., str]
) -> None:
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from fea_core.telemetry import build_providers

    exporter = InMemorySpanExporter()
    tracer_provider, meter_provider = build_providers("fea-core-test", "test")
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    app = create_app(
        settings,
        configure_observability=False,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )
    token = make_token()
    given = "6f1c1d0e-5b8a-4c8e-9a52-0d3a9d3c2b11"
    TestClient(app).get(
        "/v1/me?email=ana@example.com",
        headers={**bearer(token), "X-Correlation-Id": given},
    )
    TestClient(app).get("/v1/health")

    spans = exporter.get_finished_spans()
    dump = " ".join(str(s.attributes) for s in spans)
    server_spans = [s for s in spans if s.attributes and "correlation_id" in s.attributes]
    assert [s.attributes["correlation_id"] for s in server_spans if s.attributes] == [given]
    assert [s.attributes["url.query"] for s in server_spans if s.attributes] == ["[redacted]"]
    for secret in (token, "ana", "example.com"):
        assert secret not in dump
    assert "/v1/health" not in dump
