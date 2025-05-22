# AllPairs wrapper
FROM python:3.12-alpine3.21

# bash is required for dsub in the All of Us cloud environment
RUN apk add --no-cache bash

WORKDIR /AllPairs

RUN pip install networkx==3.4.2
COPY all-pairs-shortest-paths.py /AllPairs/all-pairs-shortest-paths.py
