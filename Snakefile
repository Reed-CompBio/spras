import os
import PRRunner
import shutil
import yaml
from src.util import parse_config
from src.analysis.summary import summary
from src.analysis.viz import graphspace

# TODO decide whether to use os.sep os.altsep or a fixed character for file paths
# Snakemake updated the behavior in the 6.5.0 release https://github.com/snakemake/snakemake/pull/1037
# and using the wrong separator prevents Snakemake from matching filenames to the rules that can produce them
SEP = '/'

config_file = os.path.join('config', 'config.yaml')

config, datasets, out_dir, algorithm_params, algorithm_directed = parse_config(config_file)

# Return the dataset dictionary from the config file given the label
def get_dataset(datasets, label):
    return datasets[label]

algorithms = list(algorithm_params)
dataset_labels = list(datasets.keys())

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

# Log the parameter dictionaries and the mapping from parameter indices to parameter values in a yaml file
def write_parameter_log(algorithm, logfile):
    # May want to use the previously created mapping from parameter indices
    # instead of recreating it to make sure they always correspond
    cur_params_dict = {f'params{index}': params for index, params in enumerate(algorithm_params[algorithm])}

    print(f'Writing {logfile}')
    with open(logfile,'w') as f:
        yaml.safe_dump(cur_params_dict,f)

# Read the cached algorithm parameters or dataset contents from a yaml logfile
def read_yaml_log(logfile):
    with open(logfile) as f:
        return yaml.safe_load(f)

# Log the dataset contents specified in the config file in a yaml file
def write_dataset_log(dataset, logfile):
    dataset_contents = get_dataset(datasets,dataset)

    print(f'Writing {logfile}')
    with open(logfile,'w') as f:
        yaml.safe_dump(dataset_contents,f)

# Choose the final files expected according to the config file options.
def make_final_input(wildcards):
    final_input = []

    #TODO analysis could be parsed in the parse_config() function.
    if config["analysis"]["summary"]["include"]:
        # add summary output file.
        final_input.extend(expand('{out_dir}{sep}summary-{dataset}-{algorithm_params}.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))

    if config["analysis"]["graphspace"]["include"]:
        # add graph and style JSON files.
        final_input.extend(expand('{out_dir}{sep}gs-{dataset}-{algorithm_params}.json',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}gsstyle-{dataset}-{algorithm_params}.json',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))

    if len(final_input) == 0:
        # No analysis added yet, so add reconstruction output files if they exist.
        # (if analysis is specified, these should be implicity run).
        final_input.extend(expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}.txt', out_dir=out_dir, sep=SEP, dataset=dataset_labels, algorithm_params=algorithms_with_params))

    # Create log files for the parameters and datasets
    final_input.extend(expand('{out_dir}{sep}parameters-{algorithm}.yaml', out_dir=out_dir, sep=SEP, algorithm=algorithms))
    final_input.extend(expand('{out_dir}{sep}datasets-{dataset}.yaml', out_dir=out_dir, sep=SEP, dataset=dataset_labels))

    return final_input

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule all:
    input: make_final_input

# This checkpoint is used to split log_parameters into two steps so that parameters written to a logfile in a previous
# run can be used as a disk-based cache
# The checkpoint runs every time any part of the config file is updated
# It outputs an empty flag file that log_parameters depends on
# When the checkpoint executes, it reads the prior parameter logfile from disk if one exists, compares the parameters
# for this algorithm with the current parameters in the config file, and deletes the cached logfile if the cached and
# current parameters do not match
# This creates a dependency such that log_parameters will be missing its output file after this checkpoint runs
# if the parameter logfile was stale, which ensures log_parameters will run again, writing a fresh parameter logfile
# that can signal to the reconstruct rule that the parameters changed so the algorithm needs to be run again
# TODO consider whether approximate parameter matching is needed for floating point parameters
# Currently is is intentional to have very strict matching criteria
checkpoint check_cached_parameter_log:
    input: config_file
    # A Snakemake flag file
    output: touch(os.path.join(out_dir, '.parameters-{algorithm}.flag'))
    run:
        logfile = os.path.join(out_dir, f'parameters-{wildcards.algorithm}.yaml')
        # TODO remove print statements before merging but include for now to illustrate the workflow
        print(f'Cached logfile: {logfile}')

        # May want to use the previously created mapping from parameter indices
        # instead of recreating it to make sure they always correspond
        cur_params_dict = {f'params{index}': params for index, params in enumerate(algorithm_params[wildcards.algorithm])}

        # Read the cached parameters from the logfile if it exists and is readable
        try:
            cached_params_dict = read_yaml_log(logfile)
        except OSError as e:
            print(e)
            cached_params_dict = {}

        # TODO could also use this checkpoint to delete downstream files that relied on parameter indices that no
        # longer exist but it would be difficult to manually identify all of the dependencies
        print(f'Current params: {cur_params_dict}')
        print(f'Cached params: {cached_params_dict}')
        if cur_params_dict != cached_params_dict and os.path.isfile(logfile):
            print(f'Deleting stale {logfile}')
            os.remove(logfile)
        # TODO remove when removing print statements
        elif not os.path.isfile(logfile):
            print(f'Logfile {logfile} does not exist')
        else:
            print(f'Reusing cached parameters in {logfile}')

# Write the mapping from parameter indices to parameter dictionaries if the parameters changed
rule log_parameters:
    # Mark the flag as ancient so that its timestamp is always considered to be older than the output file
    # Therefore, this rule is triggered when the output file is missing but not when the input flag has been updated,
    # which happens every time any part of the config file is updated
    input: ancient(os.path.join(out_dir, '.parameters-{algorithm}.flag'))
    output: logfile = os.path.join(out_dir, 'parameters-{algorithm}.yaml')
    run:
        write_parameter_log(wildcards.algorithm, output.logfile)

# This checkpoint is used to split log_datasets into two steps so that dataset contents written to a logfile in a
# previous run can be used as a disk-based cache
# The checkpoint runs every time any part of the config file is updated
# It outputs an empty flag file that log_datasets depends on
# When the checkpoint executes, it reads the prior dataset logfile from disk if one exists, compares the dataset with
# the current dataset contents in the config file, and deletes the cached logfile if the cached and current dataset
# do not match
# This creates a dependency such that log_datasets will be missing its output file after this checkpoint runs
# if the dataset logfile was stale, which ensures log_datasets will run again, writing a fresh dataset logfile
# that can signal to the merge_input rule and downstream rules that the dataset changed
checkpoint check_cached_dataset_log:
    input: config_file
    # A Snakemake flag file
    output: touch(os.path.join(out_dir, '.datasets-{dataset}.flag'))
    run:
        logfile = os.path.join(out_dir, f'datasets-{wildcards.dataset}.yaml')
        # TODO remove print statements before merging but include for now to illustrate the workflow
        print(f'Cached logfile: {logfile}')

        cur_dataset_dict = get_dataset(datasets, wildcards.dataset)

        # Read the cached dataset from the logfile if it exists and is readable
        try:
            cached_dataset_dict = read_yaml_log(logfile)
        except OSError as e:
            print(e)
            cached_dataset_dict = {}

        print(f'Current dataset: {cur_dataset_dict}')
        print(f'Cached dataset: {cached_dataset_dict}')
        if cur_dataset_dict != cached_dataset_dict and os.path.isfile(logfile):
            print(f'Deleting stale {logfile}')
            os.remove(logfile)
        # TODO remove when removing print statements
        elif not os.path.isfile(logfile):
            print(f'Logfile {logfile} does not exist')
        else:
            print(f'Reusing cached dataset in {logfile}')

# Write the datasets if the contents changed
rule log_datasets:
    # Mark the flag as ancient so that its timestamp is always considered to be older than the output file
    # Therefore, this rule is triggered when the output file is missing but not when the input flag has been updated,
    # which happens every time any part of the config file is updated
    input: ancient(os.path.join(out_dir,'.datasets-{dataset}.flag'))
    output: logfile = os.path.join(out_dir, 'datasets-{dataset}.yaml')
    run:
        write_dataset_log(wildcards.dataset, output.logfile)

# Return all files used in the dataset plus the cached dataset file, which represents the relevant part of the
# config file
# Input preparation needs to be rerun if these files are modified
def get_dataset_dependencies(wildcards):
    # Introduce a dependency between this function (which is used by the merge_input rule) and the
    # check_cached_dataset_log so that this function is re-evaluated after the checkpoint runs for this
    # wildcard value (dataset label)
    # Without the dependency, Snakemake does not rerun merge_input when the datasets contents are modified in the
    # config file
    # The dataset logfile already exists on disk, and it is not modified with a newer timestamp until after
    # the merge_input rule has been analyzed
    # The Snakemake command has to be run a second time for the merge_input rule to be analyzed again, at which point
    # Snakemake detects the merge_input input file (the dataset logfile) is newer than the output pickle file
    # and reruns merge_input and all downstream rules
    # Introducing the direct dependency here enables rerunning all downstream dependencies in a single Snakemake call
    # TODO this may be broken, triggering parse_input to rerun too frequently
    # TODO requires further testing
    checkpoints.check_cached_dataset_log.get(**wildcards)

    dataset = datasets[wildcards.dataset]
    all_files = dataset["node_files"] + dataset["edge_files"] + dataset["other_files"]
    # Add the relative file path and dataset logfile
    all_files = [dataset["data_dir"] + SEP + data_file for data_file in all_files]
    all_files.append(out_dir + SEP + f'datasets-{wildcards.dataset}.yaml')
    return all_files

# Merge all node files and edge files for a dataset into a single node table and edge table
rule merge_input:
    # Depends on the node, edge, and other files for this dataset so the rule and downstream rules are rerun if they change
    # Also depends on the relevant part of the config file
    input: get_dataset_dependencies
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
    output: output_dir = directory(os.path.join(out_dir, 'prepared', '{dataset}-{algorithm}-inputs'))
    # Run the preprocessing script for this algorithm
    run:
        # Make sure the output subdirectories exist
        os.makedirs(output.output_dir, exist_ok=True)
        # Use the algorithm's generate_inputs function to load the merged dataset, extract the relevant columns,
        # and write the output files specified by required_inputs
        # The filename_map provides the output file path for each required input file type
        filename_map = {input_type: SEP.join([out_dir, 'prepared', f'{wildcards.dataset}-{wildcards.algorithm}-inputs', f'{input_type}.txt']) for input_type in PRRunner.get_required_inputs(wildcards.algorithm)}
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
    prepared_dir = SEP.join([out_dir, 'prepared', f'{wildcards.dataset}-{wildcards.algorithm}-inputs'])

    # Construct the list of expected prepared input files for the reconstruction algorithm
    prepared_inputs = expand(f'{prepared_dir}{SEP}{{type}}.txt',type=PRRunner.get_required_inputs(algorithm=wildcards.algorithm))
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

    # The reconstruct rule also depends on the parameters
    # Add the parameter logfile to the list of inputs so that the reconstruct rule is executed if the parameters change
    prepared_inputs.append(out_dir + SEP + f'parameters-{wildcards.algorithm}.yaml')
    return prepared_inputs

# Run the pathway reconstruction algorithm
# TODO test that the reconstruct rule is not rerun if the config file changes but the parameters for this algorithm
# do not (requires setting up dataset configuration caching first)
rule reconstruct:
    input: collect_prepared_input
    output: pathway_file = os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    run:
        # Create a copy so that the updates are not written to the parameters logfile
        params = reconstruction_params(wildcards.algorithm, wildcards.params).copy()
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
