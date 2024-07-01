FROM almalinux:9

RUN dnf install -y epel-release

# gcc/g++ are required for building several of the packages if you're using apple silicon
RUN dnf update -y && \
    dnf install -y gcc gcc-c++ \
    python3.11 python3.11-pip python3.11-devel \
    docker apptainer

COPY / /spras/
RUN chmod -R 777 /spras
WORKDIR /spras

# Install spras into the container
RUN pip3.11 install .
