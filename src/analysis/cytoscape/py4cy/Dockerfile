FROM python:3.9.13
RUN pip install py4cytoscape==1.3.0

# PARAMETERS
ENV CYTOSCAPE_VERSION 3.9.1

# CHANGE USER
USER root

# INSTALL JAVA
RUN apt-get update && apt-get -y install default-jdk libxcursor1 xvfb supervisor wget x11vnc novnc websockify
RUN cd / && wget https://github.com/cytoscape/cytoscape/releases/download/${CYTOSCAPE_VERSION}/cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz \
    && tar xf cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz && rm cytoscape-unix-${CYTOSCAPE_VERSION}.tar.gz
RUN cd /cytoscape-unix-${CYTOSCAPE_VERSION}/framework/system/org/cytoscape/property-impl/${CYTOSCAPE_VERSION} \
    && jar -xf property-impl-${CYTOSCAPE_VERSION}.jar cytoscape3.props \
    && cat cytoscape3.props | sed "s/^cyrest.version.*/cyrest.version=3.12.3/g" > cytoscape3.props.tmp \
    && mv cytoscape3.props.tmp cytoscape3.props \
    && jar -uf property-impl-${CYTOSCAPE_VERSION}.jar cytoscape3.props \
    && rm cytoscape3.props \
    && cd /
# Set JAVA_HOME From sudo update-alternatives --config java
RUN echo 'JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"' >> /etc/environment

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY cytoscape_util.py /spras/cytoscape_util.py
CMD ["/usr/bin/supervisord"]