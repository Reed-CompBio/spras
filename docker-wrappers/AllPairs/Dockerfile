# AllPairs wrapper
FROM python:3.12-alpine3.21
LABEL org.opencontainers.image.source=https://github.com/Reed-CompBio/spras

# bash is required for dsub in the All of Us cloud environment
RUN apk add --no-cache bash

WORKDIR /AllPairs

RUN pip install networkx==3.4.2
RUN wget -O /AllPairs/all-pairs-shortest-paths.py https://raw.githubusercontent.com/Reed-CompBio/all-pairs-shortest-paths/b4fcc4f7d665a51213488e93b4664afbe4eca6c1/allpairs.py
