# The following docker image is derived from a containerized version
# of Cytoscape with GUI support
# 
# https://github.com/cytoscape/docker-cytoscape-desktop

FROM ubuntu:20.04

# PARAMETERS
ENV CYTOSCAPE_VERSION=3.9.1

# CHANGE USER
USER root

# https://github.com/cytoscape/cytoscape/releases/download/3.8.2/cytoscape-unix-3.8.2.tar.gz
# INSTALL JAVA
RUN apt-get update && apt-get -y install default-jdk libxcursor1 xvfb supervisor wget x11vnc
RUN wget https://github.com/cytoscape/cytoscape/releases/download/${CYTOSCAPE_VERSION}/cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz
RUN tar xf cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz && rm cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz

# Set JAVA_HOME From sudo update-alternatives --config java
RUN echo 'JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"' >> /etc/environment

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

ENV PATH /opt/conda/bin:$PATH
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.3-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean --all && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    conda init bash

COPY src/analysis/cytoscape/env.yml /docker/minimal_env.yml
RUN conda env create -f /docker/minimal_env.yml

COPY src/analysis/cytoscape/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 1234 5900

CMD ["/usr/bin/supervisord > /dev/null 2>&1"]