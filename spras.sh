#!/bin/bash

if (($# == 0)); then
    echo "usage: bash spras.sh --config [config.yml] --cores[int]--cytoscape[OPTIONAL]"
    exit 0
fi

POSITIONAL_ARGS=()
HELP_MSG=NO
USE_CYTOSCAPE=NO

while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--config)
      CONFIG="$2"
      shift # past argument
      shift # past value
      ;;
    --cores)
      CORES="$2"
      shift # past argument
      shift # past value
      ;;
    -y|--cytoscape)
      USE_CYTOSCAPE=YES
      shift # past argument
      ;;
    --help)
      HELP_MSG=YES
      shift # past argument with no value
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done
set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

if [ ${HELP_MSG} == YES ]; then
	echo "usage: bash spras.sh --config [config.yml] --cytoscape[OPTIONAL]"
	exit 0
fi

echo "CONFIG FILE           = ${CONFIG}"
echo "CORES                 = ${CORES}"

if [[ -n $1 ]]; then
    echo "error: invalid arguments"
    echo "usage: bash spras.sh --config [config.yml] --cytoscape[OPTIONAL]"
    exit 0
fi

echo "activate SPRAS environment"
eval "$(conda shell.bash hook)"
conda activate spras

if [ $? -ne 0 ]; then
   	echo "environment does not exist"
	echo "creating SPRAS environment"
	conda env create -f environment.yml
	conda activate tps_workflow
fi
echo "environment activated"
 
snakemake --cores ${CORES} --configfile ${CONFIG}

echo "deactivate spras env"
conda deactivate

echo "activate py2cytoscape env"
conda activate py2cytoscape_env

if [ $? -ne 0 ]; then
   	echo "environment does not exist"
	echo "creating SPRAS environment"
	conda env create -f cytoscape_env.yml
	conda activate py2cytoscape_env
fi

python cytoscape.py
