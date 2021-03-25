# Omics Integrator 2 wrapper
# https://github.com/fraenkel-lab/OmicsIntegrator2
# Activates the conda environment before running command inside container
# Uses the strategy from https://pythonspeed.com/articles/activate-conda-dockerfile/
# by Itamar Turner-Trauring
FROM continuumio/miniconda3

COPY environment.yml .
RUN conda env create -f environment.yml

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "oi2"]
