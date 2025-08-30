FROM python:3.8-bullseye
LABEL org.opencontainers.image.source=https://github.com/Reed-CompBio/spras

WORKDIR /btb
RUN wget https://raw.githubusercontent.com/Reed-CompBio/BowTieBuilder-Algorithm/dd8519cd8a8397c0e0724106f498b6002d3f7be2/btb.py
RUN pip install networkx==2.8