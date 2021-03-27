# Omics Integrator 1 wrapper
# https://github.com/fraenkel-lab/OmicsIntegrator
# Activates the conda environment before running command inside container
# Uses the strategy from https://pythonspeed.com/articles/activate-conda-dockerfile/
# by Itamar Turner-Trauring
FROM continuumio/miniconda3

# Need to install msgsteiner-1.3 and dependencies

COPY environment.yml .
RUN conda env create -f environment.yml

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "oi1"]
