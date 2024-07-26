#uses ubuntu as the base
FROM python:3.10.7-alpine

# gettext is required for the envsubst command
# See https://github.com/haskell/cabal/issues/6126 regarding wget
RUN apk add --no-cache ca-certificates gettext wget

WORKDIR /ResponseNet

COPY responsenet-files.txt .

RUN export RESPONSENET_COMMIT_SHA=fd1e2b1cff6fd5c4bf84ac40800dc4feba487b8a
RUN envsubst '${RESPONSENET_COMMIT_SHA}' < responsenet-files.txt > responsenet-files-versioned.txt
RUN rm responsenet-files.txt
RUN wget --input-file responsenet-files-versioned.txt
RUN sed -i '/pkg-resources/d' requirements.txt && \
    pip install -r requirements.txt