FROM python:3.11.5
LABEL org.opencontainers.image.source=https://github.com/Reed-CompBio/spras

# Required for PageRank to run
RUN pip install networkx==2.8.8 numpy==1.26.4 scipy==1.15.2

WORKDIR /ST_RWR

RUN wget https://raw.githubusercontent.com/Reed-CompBio/rwr/9de14ac239df906f5ed0c19b9a42b83f5aa6f296/ST_RWR.py
