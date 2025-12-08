FROM python:3.8-alpine

RUN apk add --no-cache git

WORKDIR /btb
RUN wget https://raw.githubusercontent.com/Reed-CompBio/BowTieBuilder-Algorithm/dd8519cd8a8397c0e0724106f498b6002d3f7be2/btb.py
RUN pip install networkx==2.8
