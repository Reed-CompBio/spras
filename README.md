# pathway-reconstruction-enhancer

This repo is a first-start at a dockerized library of pathway reconstruction enhancement tools. See the [Running Notes of Joint Meetings](https://docs.google.com/document/d/1bAiq3JpLOHU15p1eycm6XvvdYvBxQEB5zXcrWZhLTac/edit?usp=sharing).

## Work Log

**9/2020** -- CLI draft, following the [Ontology of Pathway Reconstruction](https://docs.google.com/document/d/11gJeQf9sphP4oRz1FQYRxewxfVvNyXqbwOkeq9VxikI/edit?pli=1#bookmark=id.86waxedse4i) google doc.

```
python3 CLI_template.py --full-help
```

Questions (some of which may be in the Google Doc already):
- What should `prepare-infiles` do?  Should it be revealed to the user?  We have a universal format to reconstruction methods - this could end up as a file converter step.
- It is more efficient to loading the network file and run multiple pathways (sources/targets/nodes) and/or run multiple algorithms (oi2,pathlinker,etc.). How should the CLI/snakemake handle this?  Snakemake + a config file may do the job.  Otherwise, we want the simplest ways to run algs.
- In general, which subcalls should be parallelizable?
- For `parse-outputs`, any options? What is this output format?
- Next up, consider snakemake as an option.


## Other References

- BEELINE [[github source]](https://github.com/Murali-group/Beeline) [[documentation]](https://murali-group.github.io/Beeline/BEELINE.html#beeline)

## Name Ideas?

The name can _definitely_ change.

- Pathway Reconstruction enHANCER --> prancer
- add more!
