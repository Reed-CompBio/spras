# PathLinker wrapper
# https://github.com/fraenkel-lab/OmicsIntegrator2
# Activates the conda environment before running command inside container
# Uses the strategy from https://pythonspeed.com/articles/activate-conda-dockerfile/
# by Itamar Turner-Trauring
FROM continuumio/miniconda3:4.9.2

RUN apt-get -qq update && \
    apt-get install -y gettext-base

COPY environment.yml .
RUN conda env create -f environment.yml

WORKDIR /home/PathLinker
COPY pathlinker-files.txt .
RUN export PATHLINKER_COMMIT_SHA=d4a44c9f44f4afe30fd945015d84c1ce8c602c00 && \
    envsubst '${PATHLINKER_COMMIT_SHA}' < pathlinker-files.txt > pathlinker-files-versioned.txt && \
    rm pathlinker-files.txt && \
    wget --input-file pathlinker-files-versioned.txt

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "pathlinker"]
