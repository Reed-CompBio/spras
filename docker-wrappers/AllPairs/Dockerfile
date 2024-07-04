# AllPairs wrapper
FROM python:3.9-alpine3.16

# bash is required for dsub in the All of Us cloud environment
RUN apk add --no-cache bash

WORKDIR /AllPairs

RUN pip install networkx==2.6.3
COPY all-pairs-shortest-paths.py /AllPairs/all-pairs-shortest-paths.py
