# DOMINO wrapper
# https://github.com/Shamir-Lab/DOMINO
FROM python:3.7

WORKDIR /DOMINO
RUN pip install domino-python

RUN mkdir -p /DOMINO/src/data
WORKDIR /DOMINO/src/data

RUN wget https://raw.githubusercontent.com/Shamir-Lab/DOMINO/master/src/data/ensg2gene_symbol.txt && \
    wget https://raw.githubusercontent.com/Shamir-Lab/DOMINO/master/src/data/ensmusg2gene_symbol.txt && \
    wget https://raw.githubusercontent.com/Shamir-Lab/DOMINO/master/src/data/graph.html.format
