FROM python:3.11.5

# Required for PageRank to run
RUN pip install networkx==2.8.8 numpy==1.26.4 scipy==1.15.2

WORKDIR /ST_RWR

RUN wget https://raw.githubusercontent.com/Reed-CompBio/rwr/bb8d61069376afa7ff1acb47f47b34589f025d6f/ST_RWR.py
