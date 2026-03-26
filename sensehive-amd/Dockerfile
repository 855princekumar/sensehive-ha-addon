ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip git

WORKDIR /app

RUN git clone https://github.com/855princekumar/sense-hive.git .

RUN pip3 install -r requirements.txt

CMD ["python3", "app.py"]