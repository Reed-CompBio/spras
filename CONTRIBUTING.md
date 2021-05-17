# Contributing a new pathway reconstruction algorithm
1. One a [GitHub issue](https://github.com/Reed-CompBio/spras/issues/new/choose) to propose adding a new algorithm and discuss it with the SPRAS maintainers
1. Add a new subdirectory to `docker-wrappers` with the name `<algorithm>`, write a `Dockerfile` to build an image for `<algorithm>`, and include any other files required to build that image in the subdirectory
1. Build and push the Docker image to the (`reedcompbio`)[https://hub.docker.com/orgs/reedcompbio] Docker organization (SPRAS maintainer required)
1. Add a new Python file `src/<algorithm>.py` to implement the wrapper functions for `<algorithm>`: specify the list of `required_input` files and the `generate_inputs`, `run`, and `parse_output` functions
1. Import the new class in `PRRunner.py` so the wrapper functions can be accessed
1. Document the usage of the Docker wrapper and the assumptions made when implementing the wrapper
1. Add example usage for the new algorithm and its parameters to the template config file
1. Write test functions and provide example input data in a new test subdirectory `test/<algorithm>`
1. Extend `.github/workflows/test-docker-wrappers.yml` to pull and build the new Docker image
