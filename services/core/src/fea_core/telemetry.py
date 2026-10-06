from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from structlog.typing import EventDict, WrappedLogger


def configure_tracing(service_name: str, environment: str) -> None:
    resource = Resource.create(
        {"service.name": service_name, "deployment.environment": environment}
    )
    trace.set_tracer_provider(TracerProvider(resource=resource))


def add_trace_context(_logger: WrappedLogger, _method: str, event_dict: EventDict) -> EventDict:
    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        event_dict["trace_id"] = format(context.trace_id, "032x")
        event_dict["span_id"] = format(context.span_id, "016x")
    return event_dict
