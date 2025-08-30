# Omics Integrator 2 wrapper
# https://github.com/fraenkel-lab/OmicsIntegrator2
FROM continuumio/miniconda3:4.9.2
LABEL org.opencontainers.image.source=https://github.com/Reed-CompBio/spras

COPY environment.yml .
RUN conda env update --name base --file environment.yml --prune
