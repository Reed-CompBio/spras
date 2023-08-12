# DOMINO wrapper
# https://github.com/Shamir-Lab/DOMINO
FROM python:3.7

RUN pip install domino-python==0.1.1

# DOMINO requires data files in hard-coded locations
RUN cd /usr/local/lib/python3.7/site-packages/src/data && \
    wget https://raw.githubusercontent.com/Shamir-Lab/DOMINO/master/src/data/ensg2gene_symbol.txt && \
    wget https://raw.githubusercontent.com/Shamir-Lab/DOMINO/master/src/data/ensmusg2gene_symbol.txt && \
    wget https://raw.githubusercontent.com/Shamir-Lab/DOMINO/master/src/data/graph.html.format
