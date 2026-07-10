FROM almalinux:9

# gcc/g++ are required for building several of the packages if you're using apple silicon
RUN dnf update -y && \
    dnf install -y epel-release && \
    dnf install -y gcc gcc-c++ \
    python3.13 python3.13-pip python3.13-devel \
    docker apptainer && \
    dnf clean all

COPY / /spras/
RUN chmod -R 777 /spras
WORKDIR /spras

# Install spras into the container
RUN pip3.13 install .
