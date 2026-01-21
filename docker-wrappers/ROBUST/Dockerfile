FROM python:3.7.17

COPY requirements.txt .

RUN COMMIT_SHA_ROBUST=9f1d30f69dcd826579ceea4e4d3b91730c2c343b && \
    wget https://github.com/bionetslab/robust_bias_aware/tarball/$COMMIT_SHA_ROBUST && \
    tar -zxvf $COMMIT_SHA_ROBUST && \
    rm $COMMIT_SHA_ROBUST && \
    mv bionetslab-robust_bias_aware-* ROBUST && \
    cd ROBUST && \
    pip install -r /requirements.txt
