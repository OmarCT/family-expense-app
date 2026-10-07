from fastapi.telemetry import TelemetryConfig
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Span, SpanProcessor, TracerProvider
from starlette.types import Scope
from structlog.typing import EventDict, WrappedLogger

EXCLUDED_PATHS = frozenset({"/v1/health"})
REDACTED = "[redacted]"


class QueryRedactor(SpanProcessor):
    """La consulta puede llevar datos personales y FastAPI solo oculta parámetros conocidos."""

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        if span.attributes and "url.query" in span.attributes:
            span.set_attribute("url.query", REDACTED)


def build_providers(service_name: str, environment: str) -> tuple[TracerProvider, MeterProvider]:
    resource = Resource.create(
        {"service.name": service_name, "deployment.environment": environment}
    )
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(QueryRedactor())
    return tracer_provider, MeterProvider(resource=resource)


def _skip_health(scope: Scope) -> bool:
    return scope.get("path") in EXCLUDED_PATHS


def telemetry_config(
    tracer_provider: TracerProvider | None, meter_provider: MeterProvider | None = None
) -> TelemetryConfig:
    """Configuración de la telemetría nativa de FastAPI.

    Los exportadores OTLP los añade FastAPI desde OTEL_EXPORTER_OTLP_ENDPOINT. Los logs
    nativos quedan apagados: incluirían mensajes de excepción y trazas de pila, que pueden
    llevar datos personales (regla 7).
    """
    if tracer_provider is None:
        return {"auto_configure": False, "tracing": False, "metrics": False, "logs": False}
    config: TelemetryConfig = {"tracer_provider": tracer_provider, "logs": False}
    if meter_provider is not None:
        config["meter_provider"] = meter_provider
    config["exclude"] = _skip_health
    return config


def configure_tracing(service_name: str, environment: str) -> tuple[TracerProvider, MeterProvider]:
    tracer_provider, meter_provider = build_providers(service_name, environment)
    trace.set_tracer_provider(tracer_provider)
    return tracer_provider, meter_provider


def add_trace_context(_logger: WrappedLogger, _method: str, event_dict: EventDict) -> EventDict:
    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        event_dict["trace_id"] = format(context.trace_id, "032x")
        event_dict["span_id"] = format(context.span_id, "016x")
    return event_dict
