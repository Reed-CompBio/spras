# With Git Bash on Windows multiline strings are not executed properly
# https://carpentries-incubator.github.io/workflows-snakemake/07-resources/index.html
# (No longer applicable for this command, but a good reminder)

import os
import PRRunner
from src.util import parse_config
from src.analysis.summary import summary
from src.analysis.viz import graphspace

config_file = os.path.join('config', 'config.yaml')
wildcard_constraints:
    algorithm='\w+'

config, datasets, out_dir, algorithm_params, algorithm_directed = parse_config(config_file)

# Return the dataset dictionary from the config file given the label
def get_dataset(datasets, label):
    #return datasets[dataset_dict[label]]
    return datasets[label]

# Return all files used in the dataset plus the config file
# TODO Consider how to make the dataset depend only on the part of the config file relevant for this dataset
# instead of the entire config file
# Input preparation needs to be rerun if these files are modified
def get_dataset_dependencies(datasets, label):
    dataset = datasets[label]
    all_files = dataset["node_files"] + dataset["edge_files"] + dataset["other_files"]
    # Add the relative file path and config file
    all_files = [os.path.join(dataset["data_dir"], data_file) for data_file in all_files]
    return all_files + [config_file]

algorithms = list(algorithm_params.keys())
#pathlinker_params = algorithm_params['pathlinker'] # Temporary

# Eventually we'd store these values in a config file
#run_options = {}
#run_options["augment"] = False
#run_options["parameter-advise"] = False

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

def write_dataset_log(dataset,logfile):
    with open(logfile,'w') as f:
        for key,value in datasets[dataset].items():
            f.write(f'{key}: {value}\n')


# Choose the final input for reconstruct_pathways based on which options are being run
# Right now this is a static run_options dictionary but would eventually
# be done with the config file
def make_final_input(wildcards):
    '''
    # Commenting out code that considers augment or parameter advising, since we don't yet handle that.
    #
    # Right now this lets us do ppa or augmentation, but not both.
    # An easy solution would be to make a separate rule for doing both, but
    # if we add more things to do after the fact that will get
    # out of control pretty quickly. Steps run in parallel won't have this problem, just ones
    # whose inputs depend on each other.
    # Currently, this will not re-generate all of the individual pathways
    # when augmenting or advising
    # Changes to the parameter handling may have broken the augment and advising options
    if run_options["augment"]:
        final_input = expand('{out_dir}{sep}augmented-pathway-{dataset}-{algorithm}-{params}.txt', out_dir=out_dir, sep=os.sep, dataset=dataset_labels, algorithm=algorithms, params=pathlinker_params)
    elif run_options["parameter-advise"]:
        #not a great name
        final_input = expand('{out_dir}{sep}advised-pathway-{dataset}-{algorithm}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms)
    else:
        # Temporary, build up one rule at a time to help debugging
        # dynamic() may not work when defined in a separate function
        #final_input = dynamic(expand('{out_dir}{sep}{dataset}-{algorithm}-{{type}}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys(), algorithm=algorithms))
        # Use 'params<index>' in the filename instead of describing each of the parameters and its value
        final_input = expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys(), algorithm_params=algorithms_with_params)
        # Create log files for the parameter indices
        #final_input.extend(expand('{out_dir}{sep}parameters-{algorithm}.txt', out_dir=out_dir, sep=os.sep, algorithm=algorithms))
    '''
    final_input = []

    #TODO analysis could be parsed in the parse_config() function.
    if config["analysis"]["summary"]["include"]:
        # add summary output file.
        final_input.extend(expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}-summary.txt',out_dir=out_dir,sep=os.sep,dataset=datasets,algorithm_params=algorithms_with_params))

    if config["analysis"]["graphspace"]["include"]:
        # add graph and style JSON files.
        final_input.extend(expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}-gs.json',out_dir=out_dir,sep=os.sep,dataset=datasets,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}-gs-style.json',out_dir=out_dir,sep=os.sep,dataset=datasets,algorithm_params=algorithms_with_params))

    if len(final_input) == 0:
        # No analysis added yet, so add reconstruction output files if they exist.
        # (if analysis is specified, these should be implicity run).
        final_input.extend(expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys(), algorithm_params=algorithms_with_params))

    # Create log files for the parameters and datasets
    final_input.extend(expand('{out_dir}{sep}parameters-{algorithm}.txt', out_dir=out_dir, sep=os.sep, algorithm=algorithms))
    final_input.extend(expand('{out_dir}{sep}datasets-{dataset}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys()))

    return final_input

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule reconstruct_pathways:
    input: make_final_input
    # dynamic() may not work when defined in a separate function but may not be needed if not running the
    # prepare_input rule directly
    #input: dynamic(expand('{out_dir}{sep}{dataset}-{algorithm}-{{type}}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys(), algorithm=algorithms))

# Merge all node files and edge files for a dataset into a single node table and edge table
rule merge_input:
    # Depends on the node, edge, and other files for this dataset so the rule and downstream rules are rerun
    # if they change
    # Also depends on the config file
    # TODO does not need to depend on the entire config file but rather only the input files for this dataset
    # TODO why does this pass datasets while datasets is in the global frame as well?
    input: lambda wildcards: get_dataset_dependencies(datasets, wildcards.dataset)
    output: dataset_file = os.path.join(out_dir, '{dataset}-merged.pickle')
    run:
        # Pass the dataset to PRRunner where the files will be merged and written to disk (i.e. pickled)
        dataset_dict = get_dataset(datasets, wildcards.dataset)
        PRRunner.merge_input(dataset_dict, output.dataset_file)

# Universal input to pathway reconstruction-specific input
# Functions are not allowed when defining the output file list ("Only input files can be specified as functions" error)
# An alternative could be to dynamically generate one rule per reconstruction algorithm
# See https://stackoverflow.com/questions/48993241/varying-known-number-of-outputs-in-snakemake
# Currently using dynamic() to indicate we do not know in advance statically how many {type} values there will be
# See https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#dynamic-files
# See https://groups.google.com/g/snakemake/c/RO71QYIJ49E
# The number of steps cannot be estimated accurately statically so the Snakemake output contains messages like
# '6 of 4 steps (150%) done'
# TODO consider alternatives for the dynamic output file list
rule prepare_input:
    input: dataset_file = os.path.join(out_dir, '{dataset}-merged.pickle')
    # Could ideally use required_inputs to determine which output files to write
    # That does not seem possible because it requires a function and is not static
    output: output_files = dynamic(os.path.join(out_dir, 'prepared-{dataset}-{algorithm}-{type}.txt'))
    # Run the preprocessing script for this algorithm
    run:
        # Use the algorithm's generate_inputs function to load the merged dataset, extract the relevant columns,
        # and write the output files specified by required_inputs
        # The filename_map provides the output file path for each required input file type
        filename_map = {input_type: os.path.join(out_dir, f'prepared-{wildcards.dataset}-{wildcards.algorithm}-{input_type}.txt') for input_type in PRRunner.get_required_inputs(wildcards.algorithm)}
        PRRunner.prepare_inputs(wildcards.algorithm, input.dataset_file, filename_map)

# See https://stackoverflow.com/questions/46714560/snakemake-how-do-i-use-a-function-that-takes-in-a-wildcard-and-returns-a-value
# for why the lambda function is required
# Run the pathway reconstruction algorithm
rule reconstruct:
    input: lambda wildcards: expand(os.path.join(out_dir, 'prepared-{{dataset}}-{{algorithm}}-{type}.txt'), type=PRRunner.get_required_inputs(algorithm=wildcards.algorithm))
    output: pathway_file = os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    run:
        params = reconstruction_params(wildcards.algorithm, wildcards.params)
        # Add the input files
        params.update(dict(zip(PRRunner.get_required_inputs(wildcards.algorithm), *{input})))
        # Add the output file
        # TODO may need to modify the algorithm run functions to expect the output filename in the same format
        # All can accept a relative pathway to the output file that should be written that is called 'output_file'
        params['output_file'] = output.pathway_file
        PRRunner.run(wildcards.algorithm, params)

# Original pathway reconstruction output to universal output
# Use PRRunner as a wrapper to call the algorithm-specific parse_output
rule parse_output:
    input: raw_file = os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    output: standardized_file = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    # run the post-processing script
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
        
'''
# Pathway Augmentation
rule augment_pathway:
    input: os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    output: os.path.join(out_dir, 'augmented-pathway-{dataset}-{algorithm}-{params}.txt')
    shell: 'echo {input} >> {output}'

# Pathway Parameter Advising
rule parameter_advise:
    input: expand('{out_dir}{sep}pathway-{dataset}-{algorithm}-{params}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms, params=pathlinker_params)
    output: os.path.join(out_dir, 'advised-pathway-{dataset}-{algorithm}.txt')
    shell: 'echo {input} >> {output}'
'''

# Collect Summary Statistics
rule summarize:
    input:
        standardized_file = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    output:
        summary_file = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}-summary.txt')
    run:
        summary.run(input.standardized_file,output.summary_file,directed=algorithm_directed[wildcards.algorithm])

# Write GraphSpace JSON Graphs
rule viz_graphspace:
    input: standardized_file = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    output:
        graph_json = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}-gs.json'), style_json = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}-gs-style.json')
    run:
        json_prefix = os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}')
        graphspace.write_json(input.standardized_file,output.graph_json,output.style_json,directed=algorithm_directed[wildcards.algorithm])

# Remove the output directory
rule clean:
    shell: f'rm -rf {out_dir}'
