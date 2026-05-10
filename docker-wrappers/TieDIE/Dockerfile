FROM python:2.7.15

WORKDIR /TieDIE

COPY requirements.txt .
RUN pip install -r requirements.txt && \
    commit=c64ab5c4b4e0f6cfac4b5151c7d9f1d7ea331e65 && \
    wget https://github.com/Reed-CompBio/TieDIE/tarball/$commit && \
    tar -zxvf $commit && \
    rm $commit && \
    mv Reed-CompBio-TieDIE-*/* .
