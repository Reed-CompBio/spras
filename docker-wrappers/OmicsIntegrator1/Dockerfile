# Omics Integrator 1 wrapper
# https://github.com/fraenkel-lab/OmicsIntegrator
# This version does not use conda
FROM debian:12.11-slim
LABEL org.opencontainers.image.source=https://github.com/Reed-CompBio/spras

# The official Python 2.7 image is too old (Debian Buster is on EOL)
# to support downloading the packages we need in the next step.
# Instead, we get it manually
# (from https://stackoverflow.com/a/70866416/7589775)
# We also avoid the deadsnakes ppa, as it has since removed
# python 2.7 from its repositories
RUN apt update -y && apt upgrade -y && \
    apt-get install -y wget build-essential checkinstall libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev && \
    cd /usr/src && \
    wget https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz && \
    tar xzf Python-2.7.18.tgz && \
    cd Python-2.7.18 && \
    ./configure --enable-optimizations && \
    make install

# Need to install msgsteiner-1.3 and dependencies for OI1
RUN apt-get update && \
    apt-get install -y build-essential libx11-dev libboost-dev libboost-program-options-dev

# We also want pip
RUN python -m ensurepip --upgrade

RUN commit=0a57ede6beeef6e63b86d19898e560d62015e85d && \
    wget https://github.com/fraenkel-lab/OmicsIntegrator/tarball/$commit && \
    tar -zxvf $commit && \
    rm $commit && \
    mv fraenkel-lab-OmicsIntegrator-* OmicsIntegrator && \
    cd OmicsIntegrator/ && \
    wget http://staff.polito.it/alfredo.braunstein/code/msgsteiner-1.3.tgz && \
    tar -zxvf msgsteiner-1.3.tgz && \
    cd msgsteiner-1.3 && \
    patch Makefile ../patches/Makefile.linux.patch && \
    make

ENV MSGSTEINER_PATH=/OmicsIntegrator/msgsteiner-1.3/msgsteiner
WORKDIR /OmicsIntegrator

COPY requirements.txt .
RUN pip install -r requirements.txt