# Dockerfile derived from
# https://github.com/cytoscape/docker-cytoscape-desktop/blob/173ab46b4b5e5c148113ad0c9960a6af3fc50432/py4cytoscape/Dockerfile
# by Kozo Nishida
FROM python:3.9.13

# PARAMETERS
ENV CYTOSCAPE_VERSION=3.9.1
ENV PY4CYTOSCAPE_VERSION=1.3.0
ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"

# CHANGE USER
USER root

# INSTALL PY4CYTOSCAPE
RUN pip install py4cytoscape==${PY4CYTOSCAPE_VERSION}

# INSTALL JAVA AND CYTOSCAPE
RUN apt-get update && apt-get -y install default-jdk libxcursor1 xvfb supervisor wget
RUN cd / && wget https://github.com/cytoscape/cytoscape/releases/download/${CYTOSCAPE_VERSION}/cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz \
    && tar xf cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz && rm cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz
RUN cd /cytoscape-unix-${CYTOSCAPE_VERSION}/framework/system/org/cytoscape/property-impl/${CYTOSCAPE_VERSION} \
    && jar -xf property-impl-${CYTOSCAPE_VERSION}.jar cytoscape3.props \
    && cat cytoscape3.props | sed "s/^cyrest.version.*/cyrest.version=3.12.3/g" > cytoscape3.props.tmp \
    && mv cytoscape3.props.tmp cytoscape3.props \
    && jar -uf property-impl-${CYTOSCAPE_VERSION}.jar cytoscape3.props \
    && rm cytoscape3.props \
    && cd /

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY cytoscape_util.py /py4cytoscape/cytoscape_util.py
