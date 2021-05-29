# With Git Bash on Windows multiline strings are not executed properly
# https://carpentries-incubator.github.io/workflows-snakemake/07-resources/index.html
# (No longer applicable for this command, but a good reminder)

import os
import PRRunner
import shutil
from src.util import parse_config
from src.analysis.summary import summary
from src.analysis.viz import graphspace

config_file = os.path.join('config', 'config.yaml')
wildcard_constraints:
    algorithm='\w+'

config, datasets, out_dir, algorithm_params, algorithm_directed = parse_config(config_file)

# Return the dataset dictionary from the config file given the label
def get_dataset(datasets, label):
    return datasets[label]

# Return all files used in the dataset plus the config file
# TODO Consider how to make the dataset depend only on the part of the config
# file relevant for this dataset instead of the entire config file
# Input preparation needs to be rerun if these files are modified
def get_dataset_dependencies(datasets, label):
    dataset = datasets[label]
    all_files = dataset["node_files"] + dataset["edge_files"] + dataset["other_files"]
    # Add the relative file path and config file
    all_files = [os.path.join(dataset["data_dir"], data_file) for data_file in all_files]
    return all_files + [config_file]

algorithms = list(algorithm_params)

# Generate numeric indices for the parameter combinations
# of each reconstruction algorithms
def generate_param_counts(algorithm_params):
    algorithm_param_counts = {}
    for algorithm, param_list in algorithm_params.items():
        algorithm_param_counts[algorithm] = len(param_list)
    return algorithm_param_counts

algorithm_param_counts = generate_param_counts(algorithm_params)
algorithms_with_params = [f'{algorithm}-params{index}' for algorithm, count in algorithm_param_counts.items() for index in range(count)]

# Get the parameter dictionary for the specified
# algorithm and index
def reconstruction_params(algorithm, index_string):
    index = int(index_string.replace('params', ''))
    return algorithm_params[algorithm][index]

# Convert a parameter dictionary to a string of command line arguments
def params_to_args(params):
    args_list = [f'--{param}={value}' for param, value in params.items()]
    return ' '.join(args_list)

# Log the parameter dictionaries and the mapping from indices to parameter values
# Could write this as a YAML file
def write_parameter_log(algorithm, logfile):
    with open(logfile, 'w') as f:
        # May want to use the previously created mapping from parameter indices
        # instead of recreating it to make sure they always correspond
        for index, params in enumerate(algorithm_params[algorithm]):
            f.write(f'params{index}: {params}\n')

# Log the datasets specified in the config file.
def write_dataset_log(dataset,logfile):
    with open(logfile,'w') as f:
        for key,value in datasets[dataset].items():
            f.write(f'{key}: {value}\n')


# Choose the final files expected according to the config file options.
def make_final_input(wildcards):
    final_input = []

    #TODO analysis could be parsed in the parse_config() function.
    if config["analysis"]["summary"]["include"]:
        # add summary output file.
        final_input.extend(expand('{out_dir}{sep}summary-{dataset}-{algorithm_params}.txt',out_dir=out_dir,sep=os.sep,dataset=datasets,algorithm_params=algorithms_with_params))

    if config["analysis"]["graphspace"]["include"]:
        # add graph and style JSON files.
        final_input.extend(expand('{out_dir}{sep}gs-{dataset}-{algorithm_params}.json',out_dir=out_dir,sep=os.sep,dataset=datasets,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}gsstyle-{dataset}-{algorithm_params}.json',out_dir=out_dir,sep=os.sep,dataset=datasets,algorithm_params=algorithms_with_params))

    if len(final_input) == 0:
        # No analysis added yet, so add reconstruction output files if they exist.
        # (if analysis is specified, these should be implicity run).
        final_input.extend(expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm_params=algorithms_with_params))

    # Create log files for the parameters and datasets
    final_input.extend(expand('{out_dir}{sep}parameters-{algorithm}.txt', out_dir=out_dir, sep=os.sep, algorithm=algorithms))
    final_input.extend(expand('{out_dir}{sep}datasets-{dataset}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets))

    return final_input

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule all:
    input: make_final_input

# Merge all node files and edge files for a dataset into a single node table and edge table
rule merge_input:
    # Depends on the node, edge, and other files for this dataset so the rule and downstream rules are rerun if they change
    # Also depends on the config file
    # TODO does not need to depend on the entire config file but rather only the input files for this dataset
    # TODO why does this pass datasets while datasets is in the global frame as well?
    input: lambda wildcards: get_dataset_dependencies(datasets, wildcards.dataset)
    output: dataset_file = os.path.join(out_dir, '{dataset}-merged.pickle')
    run:
        # Pass the dataset to PRRunner where the files will be merged and written to disk (i.e. pickled)
        dataset_dict = get_dataset(datasets, wildcards.dataset)
        PRRunner.merge_input(dataset_dict, output.dataset_file)

# The checkpoint is like a rule but can be used in dynamic workflows
# The workflow directed acyclic graph is re-evaluated after the checkpoint job runs
# If the checkpoint has not executed for the provided wildcard values, it will be run and then the rest of the
# workflow will be automatically re-evaluated after if runs
# The checkpoint produces a directory instead of a list of output files because the number and types of output
# files is algorithm-dependent
checkpoint prepare_input:
    input: dataset_file = os.path.join(out_dir, '{dataset}-merged.pickle')
    # Output is a directory that will contain all prepared files for pathway reconstruction
    output: output_dir = directory(os.path.join(out_dir, 'prepared', '{dataset}-{algorithm}'))
    # Run the preprocessing script for this algorithm
    run:
        # Make sure the output subdirectories exist
        os.makedirs(output.output_dir, exist_ok=True)
        # Use the algorithm's generate_inputs function to load the merged dataset, extract the relevant columns,
        # and write the output files specified by required_inputs
        # The filename_map provides the output file path for each required input file type
        filename_map = {input_type: os.path.join(out_dir, 'prepared', f'{wildcards.dataset}-{wildcards.algorithm}', f'{input_type}.txt') for input_type in PRRunner.get_required_inputs(wildcards.algorithm)}
        PRRunner.prepare_inputs(wildcards.algorithm, input.dataset_file, filename_map)

# Collect the prepared input files from the specified directory
# If the directory does not exist for this dataset-algorithm pair, the checkpoint will detect that
# prepare_input needs to be run and will then automatically re-rerun downstream rules like reconstruct
# If the directory does exist but some of the required input files are missing, Snakemake will not automatically
# run prepare_input
# It only checks for the output of prepare_input, which is a directory
# Therefore, manually remove the entire directory if any of the expected prepared input file are missing so that
# prepare_inputs is run, the directory and prepared input files are re-generated, and the reconstruct rule is run again
# Modeled after https://evodify.com/snakemake-checkpoint-tutorial/
def collect_prepared_input(wildcards):
    # Need to construct the path in advance because it is needed before it can be obtained from the output
    # of prepare_input
    prepared_dir = os.path.join(out_dir, 'prepared', f'{wildcards.dataset}-{wildcards.algorithm}')

    # Construct the list of expected prepared input files for the reconstruction algorithm
    prepared_inputs = expand(os.path.join(prepared_dir,'{type}.txt'),type=PRRunner.get_required_inputs(algorithm=wildcards.algorithm))
    # If the directory is missing, do nothing because the missing output triggers running prepare_input
    if os.path.isdir(prepared_dir):
        # If the directory exists, confirm all prepared input files exist as well (as opposed to some or none)
        missing_inputs = False
        for input in prepared_inputs:
            if not os.path.isfile(input):
                missing_inputs = True
        # If any expected files were missing, delete the entire directory so the call below triggers running prepare_input
        if missing_inputs:
            shutil.rmtree(prepared_dir)

    # Check whether prepare_input has been run for these wildcards (dataset-algorithm pair) and run if needed
    # The check is executed by checking whether the prepare_input output exists, which is a directory
    checkpoints.prepare_input.get(**wildcards)
    return prepared_inputs

# Run the pathway reconstruction algorithm
rule reconstruct:
    input: collect_prepared_input
    output: pathway_file = os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    run:
        params = reconstruction_params(wildcards.algorithm, wildcards.params)
        # Add the input files
        params.update(dict(zip(PRRunner.get_required_inputs(wildcards.algorithm), *{input})))
        # Add the output file
        # All run functions can accept a relative path to the output file that should be written that is called 'output_file'
        params['output_file'] = output.pathway_file
        PRRunner.run(wildcards.algorithm, params)

# Original pathway reconstruction output to universal output
# Use PRRunner as a wrapper to call the algorithm-specific parse_output
rule parse_output:
    input: raw_file = os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    output: standardized_file = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    run:
        PRRunner.parse_output(wildcards.algorithm, input.raw_file, output.standardized_file)

# Write the mapping from parameter indices to parameter dictionaries
# TODO: Need this to have input files so it updates
# Possibly all rules should have the config file as input
rule log_parameters:
    output:
        logfile = os.path.join(out_dir, 'parameters-{algorithm}.txt')
    run:
        write_parameter_log(wildcards.algorithm, output.logfile)

# Write the datasets (copied from the log_parameters rule)
# TODO: Need this to have input files so it updates
# Possibly all rules should have the config file as input
rule log_datasets:
    output:
        logfile = os.path.join(out_dir, 'datasets-{dataset}.txt')
    run:
        write_dataset_log(wildcards.dataset, output.logfile)

# Collect Summary Statistics
rule summarize:
    input:
        standardized_file = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    output:
        summary_file = os.path.join(out_dir, 'summary-{dataset}-{algorithm}-{params}.txt')
    run:
        summary.run(input.standardized_file,output.summary_file,directed=algorithm_directed[wildcards.algorithm])

# Write GraphSpace JSON Graphs
rule viz_graphspace:
    input: standardized_file = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    output:
        graph_json = os.path.join(out_dir, 'gs-{dataset}-{algorithm}-{params}.json'), style_json = os.path.join(out_dir, 'gsstyle-{dataset}-{algorithm}-{params}.json')
    run:
        json_prefix = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}')
        graphspace.write_json(input.standardized_file,output.graph_json,output.style_json,directed=algorithm_directed[wildcards.algorithm])

# Remove the output directory
rule clean:
    shell: f'rm -rf {out_dir}'
