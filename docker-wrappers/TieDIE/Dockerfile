FROM python:2.7.15

RUN wget https://github.com/Lyce24/TieDIE/archive/refs/heads/master.zip && \
    unzip master.zip && \
    rm master.zip && \
    mv TieDIE-master TieDIE && \
    cd TieDIE && \
    pip install -r requirements.txt

WORKDIR /TieDIE
