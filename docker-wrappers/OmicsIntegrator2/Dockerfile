# Omics Integrator 2 wrapper
# https://github.com/fraenkel-lab/OmicsIntegrator2
FROM continuumio/miniconda3:4.9.2

COPY 0001-disable-graph-exports.patch .

RUN git clone https://github.com/agitter/OmicsIntegrator2 && \
    cd OmicsIntegrator2 && \
    git reset --hard 568f170eae388e42e923c478ac9f3308b487760b && \
    git config user.email "email@example.com" && \
    git config user.name "Non-existent User" && \
    git am /0001-disable-graph-exports.patch

COPY environment.yml .
RUN conda env update --name base --file environment.yml --prune
