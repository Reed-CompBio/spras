#uses ubuntu as the base
FROM python:3.10.7
LABEL org.opencontainers.image.source https://github.com/Reed-CompBio/spras

WORKDIR /ResponseNet

RUN pip install ortools && pip install networkx

# Commit at 8/12/25
RUN wget https://raw.githubusercontent.com/Reed-CompBio/ResponseNet/1eb9b2685af218a28af38dbcda6e5a5abca8d682/responsenet.py
