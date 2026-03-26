ARG BUILD_FROM
FROM $BUILD_FROM

# Install python
RUN apk add --no-cache python3 py3-pip

# Copy your prebuilt image content
COPY --from=devprincekumar/sense-hive:latest / /app

WORKDIR /app

CMD ["python3", "app.py"]