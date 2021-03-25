# Omics Integrator 2 Docker image

A Docker image for [Omics Integrator 2](https://github.com/fraenkel-lab/OmicsIntegrator2).

## Activating conda inside a Docker container

By default, an installed conda environment will not be activated inside the Docker container.
Docker does not invoke Bash as a login shell.
[This blog post](https://pythonspeed.com/articles/activate-conda-dockerfile/) provides a workaround demonstrated here in `Dockerfile` and `env.yml`.
It defines a custom ENTRYPOINT that uses `conda run` to run the command inside the conda environment.

To create the Docker image run:
```
docker build -t agitter/omics-integrator-2 -f Dockerfile .
```

To confirm that commands are run inside the conda environment run:
```
winpty docker run agitter/omics-integrator-2 conda list
winpty docker run agitter/omics-integrator-2 OmicsIntegrator -h
```
The `winpty` prefix is only needed on Windows.

## Testing
The `input` directory contains test files `oi2-edges.txt` and `oi2-prizes.txt`.
The Docker wrapper can be tested with the command
```
python test-oi2.py
```

However, currently this gives an error when run locally or in the Docker container
```
Traceback (most recent call last):
  File "envs/oi2/bin/OmicsIntegrator", line 8, in <module>
    sys.exit(main())
  File "envs/oi2/lib/python3.6/site-packages/OmicsIntegrator/__main__.py", line 78, in main
    vertex_indices, edge_indices = graph.pcsf()
  File "envs/oi2/lib/python3.6/site-packages/OmicsIntegrator/graph.py", line 296, in pcsf
    vertex_indices, edge_indices = pcst_fast(edges, prizes, costs, root, num_clusters, pruning, verbosity_level)
TypeError: pcst_fast(): incompatible function arguments. The following argument types are supported:
    1. (arg0: numpy.ndarray[int64], arg1: numpy.ndarray[float64], arg2: numpy.ndarray[float64], arg3: int, arg4: int, arg5: str, arg6: int) -> Tuple[numpy.ndarray[int32], numpy.ndarray[int32]]

Invoked with: array([[0, 1],
       [0, 2],
       [1, 3],
       [2, 3],
       [4, 0],
       [4, 3]]), array([1., 0., 0., 1., 0.]), array([8e+19, 8e+19, 8e+19, 8e+19, 6, 6], dtype=object), 4, 1, 'strong', 0
```

## TODO
- Attribute https://github.com/fraenkel-lab/OmicsIntegrator2
- Modify environment to use fraenkel-lab or [PyPI](https://pypi.org/project/OmicsIntegrator/) version instead of fork
- Document usage, required packages