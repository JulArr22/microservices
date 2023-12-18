FROM python:3.10-slim
RUN apt-get update -y && \
    apt-get install -y curl
ADD ./requirements.txt /code/requirements.txt
COPY app /code/app
WORKDIR /code/app
RUN pip install -r ../requirements.txt
ENTRYPOINT uvicorn --host 0.0.0.0 --port ${UVICORN_PORT} main:app
