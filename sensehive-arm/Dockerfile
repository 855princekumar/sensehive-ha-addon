ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip

COPY --from=devprincekumar/sense-hive:arm-pi5 / /app

WORKDIR /app

CMD ["python3", "app.py"]