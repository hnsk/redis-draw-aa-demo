FROM python:3.10.2-alpine
COPY ./requirements.txt ./draw.html ./websocket.py /app/
WORKDIR /app
RUN apk add gcc g++ make libffi-dev openssl-dev \
    && pip install -r requirements.txt
ENTRYPOINT [ "/usr/local/bin/uvicorn" ]
CMD [ "--host", "0.0.0.0", "websocket:app" ]
