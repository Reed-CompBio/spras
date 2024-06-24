# PathLinker wrapper
# https://github.com/Murali-group/PathLinker
FROM python:3.5.10-alpine

# gettext is required for the envsubst command
# See https://github.com/haskell/cabal/issues/6126 regarding wget
# bash is required for dsub in the All of Us cloud environment
RUN apk add --no-cache ca-certificates gettext wget bash

WORKDIR /PathLinker
COPY pathlinker-files.txt .

# Replace the template variable for the commit with the specific commit in the command below
# Download that version of the PathLinker files from GitHub, including requirements.txt
# Remove pkg-resources from requirements.txt, which cannot be installed
# Install the required Python packages with pip
RUN export PATHLINKER_COMMIT_SHA=d4a44c9f44f4afe30fd945015d84c1ce8c602c00 && \
    envsubst '${PATHLINKER_COMMIT_SHA}' < pathlinker-files.txt > pathlinker-files-versioned.txt && \
    rm pathlinker-files.txt && \
    wget --input-file pathlinker-files-versioned.txt && \
    sed -i '/pkg-resources/d' requirements.txt && \
    pip install -r requirements.txt
