import json
import logging
from datetime import datetime
from typing import Any, Dict

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.metrics import Counter
from opentelemetry.sdk.metrics import Meter, MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from settings import settings

resource: Resource = Resource.create(
    attributes={
        "service.name": "image-api",
        "service.namespace": "apis",
        "service.version": "1.0.0",
    }
)

trace.set_tracer_provider(tracer_provider=TracerProvider(resource=resource))
tracer_provider: TracerProvider = trace.get_tracer_provider()
otlp_trace_exporter = OTLPSpanExporter(
    endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
    insecure=True,
)
span_processor = BatchSpanProcessor(span_exporter=otlp_trace_exporter)
tracer_provider.add_span_processor(span_processor=span_processor)

otlp_metrics_exporter = OTLPMetricExporter(
    endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
    insecure=True,
)

metric_reader = PeriodicExportingMetricReader(
    exporter=otlp_metrics_exporter, export_interval_millis=60000
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider=meter_provider)

meter: Meter = meter_provider.get_meter(name="image-api")


def initialize_telemetry(app) -> None:
    FastAPIInstrumentor.instrument_app(app=app)
    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()


class MetricsWrapper:
    def __init__(self, meter: Meter) -> None:
        self.user_type_counter: Counter = meter.create_counter(
            name="user_type_counter",
            description="Counts the number of requests made by different user types",
            unit="count",
        )
        self.image_type_counter: Counter = meter.create_counter(
            name="image_type_counter",
            description="Counts the number of image upload requests for different image types",
            unit="count",
        )
        self.resolution_request_counter: Counter = meter.create_counter(
            name="image_resolution_request_counter",
            description="Counts the number of requests for different image resolutions",
            unit="count",
        )
        self.upload_request_counter: Counter = meter.create_counter(
            name="image_upload_request_counter",
            description="Counts the number of image upload requests",
            unit="count",
        )
        self.url_shortener_request_counter: Counter = meter.create_counter(
            name="url_shortener_request_counter",
            description="Counts the number of requests made to the URL shortener",
            unit="count",
        )

        self.most_common_short_urls_counter: Counter = meter.create_counter(
            name="most_common_short_urls",
            description="Counts the number of times a short URL is accessed",
            unit="count",
        )

    def increment_user_type(self, user_type: str) -> None:
        self.user_type_counter.add(amount=1, attributes={"user_type": user_type})

    def increment_image_type(self, image_type: str) -> None:
        self.image_type_counter.add(amount=1, attributes={"image_type": image_type})

    def increment_resolution_request(self, resolution: str) -> None:
        self.resolution_request_counter.add(
            amount=1, attributes={"resolution": resolution}
        )

    def increment_upload_request(self) -> None:
        self.upload_request_counter.add(amount=1)

    def increment_url_shortener_request(self, request_type) -> None:
        self.url_shortener_request_counter.add(
            amount=1, attributes={"request_type": request_type}
        )

    def increment_most_common_short_urls(
        self, short_id: str, original_url: str
    ) -> None:
        self.most_common_short_urls_counter.add(
            amount=1, attributes={"short_id": short_id, "original_url": original_url}
        )


class JSONLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry: Dict[str, Any] = {
                "timestamp": datetime.now().isoformat() + "Z",
                "name": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
                "filename": record.pathname,
                "function": record.funcName,
                "line_number": record.lineno,
            }

            if hasattr(record, "trace_id") and hasattr(record, "span_id"):
                log_entry.update(
                    {"trace_id": record.trace_id, "span_id": record.span_id}
                )

            print(json.dumps(log_entry))
        except Exception as e:
            print(f"Failed to emit log: {e}")


# Create and configure the global JSON log handler
json_handler = JSONLogHandler()
json_handler.setLevel(level=logging.INFO)

logging.basicConfig(level=logging.INFO, handlers=[json_handler])
metrics_wrapper = MetricsWrapper(meter=meter)
