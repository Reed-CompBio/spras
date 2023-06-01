FROM python:3.8-alpine

WORKDIR /RandomWalk

RUN pip install networkx
RUN apk add --update --no-cache py3-numpy
ENV PYTHONPATH=/usr/lib/python3.8/site-packages

COPY random_walk.py .