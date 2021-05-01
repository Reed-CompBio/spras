# Test activating conda environment before running command inside container
# Uses the strategy from https://pythonspeed.com/articles/activate-conda-dockerfile/
# by Itamar Turner-Trauring
FROM continuumio/miniconda3

COPY env.yml .
RUN conda env create -f env.yml

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "test"]
