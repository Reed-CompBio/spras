# Logistic PCA (logisticPCA) wrapper for SPRAS.
# The caller supplies Rscript /app/run_lpca.R and its arguments.
# Cross-validation is not supported, and no ENTRYPOINT is set.

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

# Install tested versions of required R packages including rARPACK's RSpectra backend.
# remotes finds these versions in CRAN or its archive.
# Install only required dependencies and do not upgrade previously installed ones.
# Transitive and system dependencies are not fully pinned by this Dockerfile.
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.r-project.org')); \
        install.packages('remotes'); \
        versions <- c(RSpectra = '0.16-2', rARPACK = '0.11-0', logisticPCA = '0.2'); \
        for (pkg in names(versions)) { \
            remotes::install_version(pkg, version = versions[[pkg]], \
                                     dependencies = NA, upgrade = 'never'); \
            stopifnot(packageVersion(pkg) == package_version(versions[[pkg]])); \
        }; \
        library(logisticPCA); library(rARPACK); library(RSpectra)"

COPY run_lpca.R /app/run_lpca.R

WORKDIR /app
