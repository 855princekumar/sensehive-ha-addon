ARG BUILD_FROM=devprincekumar/sense-hive:1.8.1
FROM ${BUILD_FROM}

ARG BUILD_ARCH
ARG BUILD_VERSION

COPY run.py /run.py

# Data lives in the add-on's /data folder (persistent and included in backups)
ENV DB_PATH=/data/iot_dashboard.db

LABEL \
    io.hass.name="SenseHive" \
    io.hass.description="Lightweight MQTT topic logger and dashboard" \
    io.hass.type="addon" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.version="${BUILD_VERSION}" \
    org.opencontainers.image.source="https://github.com/855princekumar/sensehive-ha-addon"

CMD ["python", "/run.py"]
