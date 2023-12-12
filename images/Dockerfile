# Testing a new dev container

FROM almalinux:9

RUN dnf install -y epel-release

RUN dnf update -y && \
    dnf install -y git gcc python3.11 python3.11-pip python3-devel \
    docker apptainer
# python38 python3-devel pip
# RUN yum clean all

#RUN git clone https://github.com/Reed-CompBio/spras.git && \
#    cd spras && \
#    pip install .[dev]
COPY / /spras/

WORKDIR /spras

RUN echo `pwd` > my-file.txt


RUN pip3.11 install .
