# LPCA (Logistic PCA) wrapper

Docker image: https://hub.docker.com/r/reedcompbio/lpca

This wrapper runs [logisticPCA](https://github.com/andland/logisticPCA)

([Landgraf & Lee, 2020](https://doi.org/10.1016/j.jmva.2020.104668)) as a SPRAS analysis step. It reduces the binary
edge-by-run matrix built from a set of pathway reconstruction outputs to a small
number of components and reports the proportion of deviance explained.

The analysis is driven by the `analysis.lpca` config block and the
`lpca_analysis` Snakemake rule, and is implemented in `spras/analysis/lpca.py`.

## Configuration

    analysis:
      lpca:
        include: false   # run the LPCA analysis per algorithm
        k: 2             # number of principal components
        m: 6             # fixed logisticPCA tuning parameter, used when cv is false
        cv: false        # true: choose m by cross-validation; false: use the fixed m

LPCA only runs for algorithms with multiple parameter combinations, so that the
binary matrix has more than one column. It also needs a reasonable number of
observations to be meaningful; very small inputs (such as the bundled example
datasets) produce degenerate results, which is why it is disabled by default.

  ### `partial_decomp`

  The LPCA wrapper always runs `logisticSVD` with `partial_decomp = TRUE`, which
  uses a truncated (rARPACK-based) decomposition instead of a full one. This is
  hardcoded rather than exposed as a parameter:

  - On small datasets it has no practical effect on the result.
  - On large datasets it is required to avoid out-of-memory (OOMKilled) errors
    that occur with the full decomposition.

  Because it is beneficial on large inputs and harmless on small ones, it is
  enabled unconditionally and is not a user-facing configuration option.

## Scripts

The image contains two R scripts under `/app`:

- `run_lpca.R <input> <output> <k> <m>`: runs logisticPCA with a fixed `m` and
  writes the scores CSV plus a sibling `<output basename>_deviance.txt`.
- `run_cv.R <input> <output> <k>`: cross-validates `m` over 1..20 and writes a
  CSV with a `best_m` column (plus a `_curve.csv` with the full CV curve). Only
  used when `cv: true`.

Both read a CSV whose first column holds row labels and whose remaining columns
are binary (0/1) features, and coerce missing values to 0.

## Dependency note

`logisticPCA` declares `ggplot2` as a hard `Imports` dependency, so building the
image compiles the ggplot2 stack. The Dockerfile installs the required Debian
system libraries for that. To build from a source CRAN mirror the `repos`
argument already points at `https://cran.r-project.org`.

## Building and publishing the image

For the SPRAS default registry to resolve the image, it must be published as
`docker.io/reedcompbio/lpca:v1`, which requires access to the `reedcompbio`
Docker Hub organization:

    docker build -t reedcompbio/lpca:v1 docker-wrappers/lpca/
    docker push reedcompbio/lpca:v1

