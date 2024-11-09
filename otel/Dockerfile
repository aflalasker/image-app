FROM otel/opentelemetry-collector-contrib:latest

COPY collector-config.yaml /etc/collector-config.yaml

EXPOSE 4317

# Set the entrypoint command to use the custom configuration file
CMD ["--config=/etc/collector-config.yaml"]
