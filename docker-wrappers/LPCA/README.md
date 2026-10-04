# LPCA (Logistic PCA) wrapper

Docker image: https://hub.docker.com/r/reedcompbio/lpca

This wrapper uses [logisticPCA](https://github.com/andland/logisticPCA)
([Landgraf & Lee, 2020](https://doi.org/10.1016/j.jmva.2020.104668)) for an
exploratory, two-dimensional comparison of reconstructed networks. It calls
`logisticPCA`, not `logisticSVD`. It supports only `k = 2` components and a fixed,
finite, strictly positive `m`. Cross-validation for automatic selection of `m`
and modifying `k` are not supported.

## Container interface

The image contains one R script, invoked explicitly by the caller:

```text
Rscript /app/run_lpca.R <input.csv> <scores.csv> <k=2> <m> <deviance.txt>
```

### Input

The CSV has a header row, a first column of nonempty, unique run identifiers,
and one column per binary edge feature. Rows are runs, not edges. The caller
must transpose the edge-by-run matrix returned by `summarize_networks` before
writing it.

This wrapper deliberately requires at least three runs, three edge features,
and three distinct binary network profiles. All feature values must be finite
numeric zeros or ones. Missing, nonnumeric, and nonbinary entries are errors.
Duplicate profiles and constant features are
retained when the input otherwise satisfies these requirements.

`k` must equal 2. `m` must be finite and strictly positive.

The default `m=6` is based on the exploratory
[LPCA-SPRAS experiments](https://github.com/Jeebjean/lpca-spras).
No single value of `m` was universally best.

### Outputs and numerical checks

The raw scores CSV contains `datapoint_labels`, `PC1`, and `PC2`, with one row
per input run and no synthetic centroid. It is an intermediate for Python's
PCA-compatible plotting and coordinate formatting, not a second public
coordinate table.

The deviance summary is a small text file:

```text
components: 2
m: <fixed positive value>
percent_deviance_explained: <100 times the package's whole-model statistic>
```

## SPRAS configuration

The `analysis.lpca` config settings are:

```yaml
analysis:
  lpca:
    include: false
    aggregate_per_algorithm: false
    k: 2
    m: 6
    labels: true
```

## Decomposition

`partial_decomp=TRUE` is always set. It uses
`rARPACK` (backed by `RSpectra`) for partial decompositions where supported. The
package can fall back to full eigendecomposition. It still constructs dense
edge-by-edge matrices, so memory use can grow quadratically with the number of
edge features. For example, the `egfr.yaml` configuration (19 runs, 18,851 edge features, `k=2`, `m=6`)
requires nearly 20GB memory. Completing this run may require modifying the memory
provided to the running container.

## Building and publishing the image

Replace `<tag>` below with the tag from `LPCA_CONTAINER_SUFFIX` in
`spras/analysis/lpca.py`. Publishing to the default registry requires access
to the `reedcompbio` Docker Hub organization:

    docker build -t "reedcompbio/lpca:<tag>" docker-wrappers/LPCA/
    docker push "reedcompbio/lpca:<tag>"

## Testing
Run the test Python script to test the Docker image
```commandline
python docker-wrappers/LPCA/test_container.py
```
Expected output will end with
```commandline
=== RESULT: 28 passed; 0 failed ===
Container exit status: 0
```

## AI
GPT 6 Astra was used to refactor these files and write the test code.
