FROM python:2.7.15

WORKDIR /TieDIE

COPY requirements.txt .
RUN pip install -r requirements.txt && \
    commit=ebc395339baef664ded1d9e93c4f060c8f69f296 && \
    wget https://github.com/epaull/TieDIE/tarball/$commit && \
    tar -zxvf $commit && \
    rm $commit && \
    mv epaull-TieDIE-*/* .
