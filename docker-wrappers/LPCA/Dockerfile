# Logistic PCA (logisticPCA) wrapper for SPRAS.
# Invoked by spras/analysis/lpca.py, which supplies the full command
# (Rscript /app/run_lpca.R ... or /app/run_cv.R ...), so no ENTRYPOINT is set.

# Pinned R version for reproducibility. Bump deliberately, not to :latest.
FROM rocker/r-base:4.4.2

LABEL org.opencontainers.image.source="https://github.com/Reed-CompBio/spras"
LABEL org.opencontainers.image.description="Logistic PCA (logisticPCA) wrapper for SPRAS"

# System libraries needed to compile ggplot2 (a hard Import of logisticPCA)
# and its dependency stack from source on Debian.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcurl4-openssl-dev \
        libssl-dev \
        libxml2-dev \
        libfontconfig1-dev \
        libfreetype6-dev \
        libpng-dev \
        libtiff5-dev \
        libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# logisticPCA is still on CRAN (last published 2016) and pulls in ggplot2.
RUN Rscript -e "install.packages(c('logisticPCA', 'rARPACK'), repos='https://cran.r-project.org')" \
    && Rscript -e "library(logisticPCA); library(rARPACK)"

COPY run_lpca.R /app/run_lpca.R
COPY run_cv.R /app/run_cv.R

WORKDIR /app