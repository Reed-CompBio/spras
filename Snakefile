# With Git Bash on Windows multiline strings are not executed properly
# https://carpentries-incubator.github.io/workflows-snakemake/07-resources/index.html
# (No longer applicable for this command, but a good reminder)

import os
import PRRunner
from src.util import parse_config

config_file = os.path.join('config', 'config.yaml')
wildcard_constraints:
    algorithm='\w+'

config, datasets, out_dir, algorithm_params = parse_config(config_file)

# TODO simply this after deciding whether labels are required or optional and whether
# datasets are a dictionary with the label as the key or a list
# Temporarily require labels
#dataset_labels = [dataset.get('label', f'dataset{index}') for index, dataset in enumerate(datasets)]
# Maps from the dataset label to the dataset list index
#dataset_dict = {dataset.get('label', f'dataset{index}'): index for index, dataset in enumerate(datasets)}

# Return the dataset dictionary from the config file given the label
def get_dataset(datasets, label):
    #return datasets[dataset_dict[label]]
    return datasets[label]

algorithms = list(algorithm_params.keys())
pathlinker_params = algorithm_params['pathlinker'] # Temporary

# Eventually we'd store these values in a config file
run_options = {}
run_options["augment"] = False
run_options["parameter-advise"] = False

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

# Choose the final input for reconstruct_pathways based on which options are being run
# Right now this is a static run_options dictionary but would eventually
# be done with the config file
def make_final_input(wildcards):
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
        final_input = dynamic(expand('{out_dir}{sep}{dataset}-{algorithm}-{{type}}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys(), algorithm=algorithms))
        # Use 'params<index>' in the filename instead of describing each of the parameters and its value
        #final_input = expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys(), algorithm_params=algorithms_with_params)
        # Create log files for the parameter indices
        #final_input.extend(expand('{out_dir}{sep}parameters-{algorithm}.txt', out_dir=out_dir, sep=os.sep, algorithm=algorithms))
        # TODO Create log files for the datasets
    return final_input

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule reconstruct_pathways:
    #input: make_final_input
    # dynamic() may not work when defined in a separate function
    input: dynamic(expand('{out_dir}{sep}{dataset}-{algorithm}-{{type}}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets.keys(), algorithm=algorithms))

# Merge all node files and edge files for a dataset into a single node table and edge table
rule merge_input:
    # TODO should depend on the node, edge, and other files for this dataset so the rule is rerun if they change
    input: config_file
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
    output: output_files = dynamic(os.path.join(out_dir, '{dataset}-{algorithm}-{type}.txt'))
    # Run the preprocessing script for this algorithm
    run:
        # Use the algorithm's generate_inputs function to load the merged dataset, extract the relevant columns,
        # and write the output files specified by required_inputs
        # The filename_map provides the output file path for each required input file type
        filename_map = {input_type: os.path.join(out_dir, f'{wildcards.dataset}-{wildcards.algorithm}-{input_type}.txt') for input_type in PRRunner.get_required_inputs(wildcards.algorithm)}
        PRRunner.prepare_inputs(wildcards.algorithm, input.dataset_file, filename_map)

# See https://stackoverflow.com/questions/46714560/snakemake-how-do-i-use-a-function-that-takes-in-a-wildcard-and-returns-a-value
# for why the lambda function is required
# Run the pathway reconstruction algorithm
rule reconstruct:
    input: lambda wildcards: expand(os.path.join(out_dir, '{{dataset}}-{{algorithm}}-{type}.txt'), type=PRRunner.get_required_inputs(algorithm=wildcards.algorithm))
    output: os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    # chain.from_iterable trick from https://stackoverflow.com/questions/3471999/how-do-i-merge-two-lists-into-a-single-list
    run:
        print(f"cur algo: {wildcards.algorithm}")
        params = reconstruction_params(wildcards.algorithm, wildcards.params)
        # Add the input files
        params.update(dict(zip(PRRunner.get_required_inputs(wildcards.algorithm), *{input})))
        # Add the output file
        # TODO may need to modify the algorithm run functions to expect the output filename in the same format
        params['output'] = {output}
        PRRunner.run(wildcards.algorithm, params)

        # No longer plan to call the runner from the shell, none of the below is needed but keep it temporarily for
        # reference until the new function call-based strategy works
#         input_args = ['--' + arg for arg in reconstruction_inputs(wildcards.algorithm)]
        # A list of the input file type and filename, for example
        # ['--sources' 'data1-pathlinker-sources.txt' ''--targets' 'data1-pathlinker-targets.txt']
#         input_args = list(it.chain.from_iterable(zip(input_args, *{input})))
#         params = reconstruction_params(wildcards.algorithm, wildcards.params)
        # A string representation of the parameters as command line arguments,
        # for example '--k=5'
#         params_args = params_to_args(params)
        # Write the command to a file instead of running it because this
        # functionality has not been implemented
#         shell('''
#             echo python command --algorithm {wildcards.algorithm} {input_args} --output {output} {params_args} >> {output}
#         ''')

# Original pathway reconstruction output to universal output
rule parse_output:
    input: os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    output: os.path.join(out_dir, 'pathway-{dataset}-{algorithm}-{params}.txt')
    # run the post-processing script
    shell:  'echo {wildcards.algorithm} {input} >> {output}'

# Write the mapping from parameter indices to parameter dictionaries
# TODO: Need this to have input files so it updates
# Possibly all rules should have the config file as input
rule log_parameters:
    output:
        logfile = os.path.join(out_dir, 'parameters-{algorithm}.txt')
    run:
        write_parameter_log(wildcards.algorithm, output.logfile)

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

# Remove the output directory
rule clean:
    shell: f'rm -rf {out_dir}'
