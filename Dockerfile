# syntax=docker/dockerfile:1
FROM python:3.10

RUN pip3 install --upgrade pip

RUN mkdir -m777 /app

COPY requirements.txt /app/requirements.txt

RUN pip3 install -r /app/requirements.txt

WORKDIR /app

COPY . /app

EXPOSE 5005
EXPOSE 8000
