# Running

To run Snakemake with a config file provided from the command line:

```
snakemake --cores 1 --configfile config/config.yaml
```

To run only one rule, use the `--until` flag. Especially useful for the `clean` rule:

```
snakemake --cores 1 --configfile config/config.yaml --until clean
```


# Testing

## To run a single function:
```
pytest test/analysis/test_analysis.py -k 'test_precrec_nodes'
```

## To print output, use the `-s` option:
```
pytest test/analysis/test_analysis.py -s -k 'test_precrec_nodes'
```
