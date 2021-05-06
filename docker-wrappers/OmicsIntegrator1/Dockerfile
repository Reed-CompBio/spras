# Omics Integrator 1 wrapper
# https://github.com/fraenkel-lab/OmicsIntegrator
# Activates the conda environment before running command inside container
# Uses the strategy from https://pythonspeed.com/articles/activate-conda-dockerfile/
# by Itamar Turner-Trauring
FROM continuumio/miniconda3:4.9.2

# Need to install msgsteiner-1.3 and dependencies
RUN apt-get -qq update && \
    apt-get install -y build-essential libx11-dev libboost-dev libboost-program-options-dev

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

COPY environment.yml .
RUN conda env create -f environment.yml

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "oi1"]
