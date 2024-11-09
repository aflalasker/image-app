# Otel

This directory contains the configuration to spin up a [Open Telemetry Collector](https://opentelemetry.io/docs/collector/).

## 1. Collector Configuration

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  azuremonitor:
  debug:
    verbosity: detailed

service:
  extensions: []
  pipelines:
    traces:
      receivers: [otlp]
      processors: []
      exporters: [debug, azuremonitor]
    metrics:
      receivers: [otlp]
      processors: []
      exporters: [debug, azuremonitor]
    logs:
      receivers: [otlp]
      processors: []
      exporters: [debug, azuremonitor]
```

### receivers

The collector sets up a receiver and listens for OTLP connections in port 4317.

### exporters

The collector exports the telemetry data to Azure Monitor and the collectors console.

The Azure Monitor exporter looks for `APPLICATIONINSIGHTS_CONNECTION_STRING` in the container environment. This is a prerequisite for exporting telemetry to Azure Monitor.

## 2. Collector Docker image

In order to avoid mounting the collector configuration as a volume to the container, a new OTEL Collector image is built with the collector configuration baked in to it.

```Dockerfile
FROM otel/opentelemetry-collector-contrib:latest

COPY collector-config.yaml /etc/collector-config.yaml

EXPOSE 4317

# Set the entrypoint command to use the custom configuration file
CMD ["--config=/etc/collector-config.yaml"]
```

## 3. Building the Docker image

If the image being built must be compatible with linux/amd64 platform. If you are building the image from a arm64 platform, run the following command from the otel directory,

1. Build the image

```bash
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t <SOURCE_ACR_SERVER_NAME>/otel-col:latest .
```

1. Login to Azure Container Registry

```bash
az acr login -n <SOURCE_ACR_SERVER_NAME>
```

3. Push the image to Azure Container Registry

```bash
docker push <SOURCE_ACR_SERVER_NAME>/otel-col:latest
```
