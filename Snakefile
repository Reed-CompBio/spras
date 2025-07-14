import os
from spras import runner
import shutil
import yaml
from spras.dataset import Dataset
from spras.evaluation import Evaluation
from spras.analysis import ml, summary, cytoscape
import spras.config as _config

# Snakemake updated the behavior in the 6.5.0 release https://github.com/snakemake/snakemake/pull/1037
# and using the wrong separator prevents Snakemake from matching filenames to the rules that can produce them
SEP = '/'

wildcard_constraints:
    params="params-\w+",
    dataset="\w+"

# Elsewhere we import this as config, but in the Snakefile, the variable config is already populated
# with the parsed config.yaml. This is done by Snakemake, which magically pipes config into this file
# without declaration!
_config.init_global(config)

out_dir = _config.config.out_dir
algorithm_params = _config.config.algorithm_params
algorithm_directed = _config.config.algorithm_directed
pca_params = _config.config.pca_params
hac_params = _config.config.hac_params
generate_kde = pca_params["kernel_density"] # TODO: decide if we need to save the kde file
FRAMEWORK = _config.config.container_framework

# Return the dataset or gold_standard dictionary from the config file given the label
def get_dataset(_datasets, label):
    return _datasets[label]

algorithms = list(algorithm_params)
algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in algorithm_params.items() for params_hash in param_combos.keys()]
dataset_labels = list(_config.config.datasets.keys())
dataset_gold_standard_pairs = [f"{dataset}-{gs_values['label']}" for gs_values in _config.config.gold_standards.values() for dataset in gs_values['dataset_labels']]

# Get algorithms that are running multiple parameter combinations
def algo_has_mult_param_combos(algo):
    return len(algorithm_params.get(algo, {})) > 1

algorithms_mult_param_combos = [algo for algo in algorithms if algo_has_mult_param_combos(algo)]

# Get the parameter dictionary for the specified
# algorithm and parameter combination hash
def reconstruction_params(algorithm, params_hash):
    index = params_hash.replace('params-', '')
    return algorithm_params[algorithm][index]

# Log the parameter dictionary for this parameter configuration in a yaml file
def write_parameter_log(algorithm, param_label, logfile):
    cur_params_dict = reconstruction_params(algorithm, param_label)

    with open(logfile,'w') as f:
        yaml.safe_dump(cur_params_dict,f)

# Log the dataset contents specified in the config file in a yaml file
def write_dataset_log(dataset, logfile):
    dataset_contents = get_dataset(_config.config.datasets,dataset)

    # safe_dump gives RepresenterError for an OrderedDict
    # config file has to convert the dataset from OrderedDict to dict to avoid this
    with open(logfile,'w') as f:
        yaml.safe_dump(dataset_contents,f)

# Choose the final files expected according to the config file options.
def make_final_input(wildcards):
    final_input = []

    if _config.config.analysis_include_summary:
        # add summary output file for each pathway
        # TODO: reuse in the future once we make summary work for mixed graphs. See https://github.com/Reed-CompBio/spras/issues/128
        # final_input.extend(expand('{out_dir}{sep}{dataset}-{algorithm_params}{sep}summary.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        # add table summarizing all pathways for each dataset
        final_input.extend(expand('{out_dir}{sep}{dataset}-pathway-summary.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels))

    if _config.config.analysis_include_cytoscape:
        final_input.extend(expand('{out_dir}{sep}{dataset}-cytoscape.cys',out_dir=out_dir,sep=SEP,dataset=dataset_labels))

    if _config.config.analysis_include_ml:
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}pca.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}pca-variance.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}hac-vertical.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}hac-clusters-vertical.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}pca-coordinates.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}hac-horizontal.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}hac-clusters-horizontal.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}ensemble-pathway.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}jaccard-matrix.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}jaccard-heatmap.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
        if generate_kde:
            final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}pca-kde.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm_params=algorithms_with_params))
      
    if _config.config.analysis_include_ml_aggregate_algo:
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-pca.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-pca-variance.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-pca-coordinates.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-hac-vertical.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-hac-clusters-vertical.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-hac-horizontal.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-hac-clusters-horizontal.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-ensemble-pathway.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-jaccard-matrix.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms))
        final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-jaccard-heatmap.png',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms))
        if generate_kde:
            final_input.extend(expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-pca-kde.txt',out_dir=out_dir,sep=SEP,dataset=dataset_labels,algorithm=algorithms_mult_param_combos))
    
    if _config.config.analysis_include_evaluation:
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-pca-chosen-pathway.txt',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-pca-chosen-pathway.png',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-curve-ensemble-nodes.png',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-curve-ensemble-nodes.txt',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))
    if _config.config.analysis_include_evaluation_aggregate_algo:
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-pca-chosen-pathway-per-algorithm.txt',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-pca-chosen-pathway-per-algorithm.png',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-curve-ensemble-nodes-per-algorithm.png',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))
        final_input.extend(expand('{out_dir}{sep}{dataset_gold_standard_pair}-eval{sep}pr-curve-ensemble-nodes-per-algorithm.txt',out_dir=out_dir,sep=SEP,dataset_gold_standard_pair=dataset_gold_standard_pairs))

    if len(final_input) == 0:
        # No analysis added yet, so add reconstruction output files if they exist.
        # (if analysis is specified, these should be implicitly run).
        final_input.extend(expand('{out_dir}{sep}{dataset}-{algorithm_params}{sep}pathway.txt', out_dir=out_dir, sep=SEP, dataset=dataset_labels, algorithm_params=algorithms_with_params))

    # Create log files for the parameters and datasets
    final_input.extend(expand('{out_dir}{sep}logs{sep}parameters-{algorithm_params}.yaml', out_dir=out_dir, sep=SEP, algorithm_params=algorithms_with_params))
    final_input.extend(expand('{out_dir}{sep}logs{sep}datasets-{dataset}.yaml', out_dir=out_dir, sep=SEP, dataset=dataset_labels))

    return final_input

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule all:
    input: make_final_input

# Write the mapping from parameter indices to parameter dictionaries
rule log_parameters:
    output: logfile = SEP.join([out_dir, 'logs', 'parameters-{algorithm}-{params}.yaml'])
    run:
        write_parameter_log(wildcards.algorithm, wildcards.params, output.logfile)

# Write the datasets logfiles
rule log_datasets:
    output: logfile = SEP.join([out_dir, 'logs', 'datasets-{dataset}.yaml'])
    run:
        write_dataset_log(wildcards.dataset, output.logfile)

# TODO document the assumption that if the dataset label does not change,
# the files listed in the dataset do not change
# This assumption is no longer checked by dataset logfile caching
# Return all files used in the dataset
# Input preparation needs to be rerun if these files are modified
def get_dataset_dependencies(wildcards):
    dataset = _config.config.datasets[wildcards.dataset]
    all_files = dataset["node_files"] + dataset["edge_files"] + dataset["other_files"]
    # Add the relative file path
    all_files = [dataset["data_dir"] + SEP + data_file for data_file in all_files]

    return all_files

# Merge all node files and edge files for a dataset into a single node table and edge table
rule merge_input:
    # Depends on the node, edge, and other files for this dataset so the rule and downstream rules are rerun if they change
    input: get_dataset_dependencies
    output: dataset_file = SEP.join([out_dir, '{dataset}-merged.pickle'])
    run:
        # Pass the dataset to PRRunner where the files will be merged and written to disk (i.e. pickled)
        dataset_dict = get_dataset(_config.config.datasets, wildcards.dataset)
        runner.merge_input(dataset_dict, output.dataset_file)

# Return all files used in the gold standard
def get_gold_standard_dependencies(wildcards):
    gs = _config.config.gold_standards[wildcards.gold_standard]
    all_files = gs["node_files"]
    all_files = [gs["data_dir"] + SEP + data_file for data_file in all_files]
    return all_files

# Merge all node files for a gold_standard into a single node table
rule merge_gs_input:
    input: get_gold_standard_dependencies
    output: gold_standard_file = SEP.join([out_dir, '{gold_standard}-merged.pickle'])
    run:
        gold_standard_dict = get_dataset(_config.config.gold_standards, wildcards.gold_standard)
        Evaluation.merge_gold_standard_input(gold_standard_dict, output.gold_standard_file)

# The checkpoint is like a rule but can be used in dynamic workflows
# The workflow directed acyclic graph is re-evaluated after the checkpoint job runs
# If the checkpoint has not executed for the provided wildcard values, it will be run and then the rest of the
# workflow will be automatically re-evaluated after if runs
# The checkpoint produces a directory instead of a list of output files because the number and types of output
# files is algorithm-dependent
checkpoint prepare_input:
    input: dataset_file = SEP.join([out_dir, '{dataset}-merged.pickle'])
    # Output is a directory that will contain all prepared files for pathway reconstruction
    output: output_dir = directory(SEP.join([out_dir, 'prepared', '{dataset}-{algorithm}-inputs']))
    # Run the preprocessing script for this algorithm
    run:
        # Make sure the output subdirectories exist
        os.makedirs(output.output_dir, exist_ok=True)
        # Use the algorithm's generate_inputs function to load the merged dataset, extract the relevant columns,
        # and write the output files specified by required_inputs
        # The filename_map provides the output file path for each required input file type
        filename_map = {input_type: SEP.join([out_dir, 'prepared', f'{wildcards.dataset}-{wildcards.algorithm}-inputs', f'{input_type}.txt']) for input_type in runner.get_required_inputs(wildcards.algorithm)}
        runner.prepare_inputs(wildcards.algorithm, input.dataset_file, filename_map)

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
    prepared_inputs = expand(f'{prepared_dir}{SEP}{{type}}.txt',type=runner.get_required_inputs(algorithm=wildcards.algorithm))
    # If the directory is missing, do nothing because the missing output triggers running prepare_input
    if os.path.isdir(prepared_dir):
        # First, check if .snakemake_timestamp, the last written file in a directory rule,
        # exists. This prevents multithreading errors if we accidentally read a directory
        # before it finishes. A proper API for querying this is opened as an issue at
        # https://github.com/snakemake/snakemake/issues/439.
        if not os.path.isfile(os.path.join(prepared_dir, '.snakemake_timestamp')):
            # Running this has two goals:
            # - If there is another thread running this, in correspondence with
            # https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#data-dependent-conditional-execution,
            # this will raise a IncompleteCheckpointException and poll again until that checkpoint is ready.
            # - If the prior Snakemake execution was forcefully terminated (and prepared_inputs didn't finish,
            # which must be the case since .snakemake_timestamp is the last file to be added),
            # we can reproduce the prepared_inputs file, allowing resilliency against unexpected crashes.
            checkpoints.prepare_input.get(**wildcards)
        else:
            # If the directory exists, confirm all prepared input files exist as well (as opposed to some or none)
            missing_inputs = []
            for input in prepared_inputs:
                if not os.path.isfile(input):
                    missing_inputs.append(input)
            # If any expected files were missing, ask to delete the entire directory so the call below triggers running prepare_input
            if len(missing_inputs) != 0:
                raise RuntimeError(f"Not all input files were provided. (Missing {missing_inputs})\n" +
                    f"To prevent multithreading errors, please remove the {prepared_inputs} directory and rerun the workflow.")

    # Check whether prepare_input has been run for these wildcards (dataset-algorithm pair) and run if needed
    # The check is executed by checking whether the prepare_input output exists, which is a directory
    checkpoints.prepare_input.get(**wildcards)

    return prepared_inputs

# Run the pathway reconstruction algorithm
rule reconstruct:
    input: collect_prepared_input
    # Each reconstruct call should be in a separate output subdirectory that is unique for the parameter combination so
    # that multiple instances of the container can run simultaneously without overwriting the output files
    # Overwriting files can happen because the pathway reconstruction algorithms often generate output files with the
    # same name regardless of the inputs or parameters, and these aren't renamed until after the container command
    # terminates
    output: pathway_file = SEP.join([out_dir, '{dataset}-{algorithm}-{params}', 'raw-pathway.txt'])
    run:
        # Create a copy so that the updates are not written to the parameters logfile
        params = reconstruction_params(wildcards.algorithm, wildcards.params).copy()
        # Add the input files
        params.update(dict(zip(runner.get_required_inputs(wildcards.algorithm), *{input}, strict=True)))
        # Add the output file
        # All run functions can accept a relative path to the output file that should be written that is called 'output_file'
        params['output_file'] = output.pathway_file
        # Remove the default placeholder parameter added for algorithms that have no parameters
        if 'spras_placeholder' in params:
            params.pop('spras_placeholder')
        params['container_framework'] = FRAMEWORK
        runner.run(wildcards.algorithm, params)

# Original pathway reconstruction output to universal output
# Use PRRunner as a wrapper to call the algorithm-specific parse_output
rule parse_output:
    input: 
        raw_file = SEP.join([out_dir, '{dataset}-{algorithm}-{params}', 'raw-pathway.txt']),
        dataset_file = SEP.join([out_dir, '{dataset}-merged.pickle'])
    output: standardized_file = SEP.join([out_dir, '{dataset}-{algorithm}-{params}', 'pathway.txt'])
    run:
        params = reconstruction_params(wildcards.algorithm, wildcards.params).copy()
        params['dataset'] = input.dataset_file
        runner.parse_output(wildcards.algorithm, input.raw_file, output.standardized_file, params)

# TODO: reuse in the future once we make summary work for mixed graphs. See https://github.com/Reed-CompBio/spras/issues/128
# Collect summary statistics for a single pathway
# rule summarize_pathway:
#     input:
#         standardized_file = SEP.join([out_dir, '{dataset}-{algorithm}-{params}', 'pathway.txt'])
#     output:
#         summary_file = SEP.join([out_dir, '{dataset}-{algorithm}-{params}', 'summary.txt'])
#     run:
#         summary.run(input.standardized_file,output.summary_file)


# Write a Cytoscape session file with all pathways for each dataset
rule viz_cytoscape:
    input: pathways = expand('{out_dir}{sep}{{dataset}}-{algorithm_params}{sep}pathway.txt', out_dir=out_dir, sep=SEP, algorithm_params=algorithms_with_params)
    output: 
        session = SEP.join([out_dir, '{dataset}-cytoscape.cys'])
    run:
        cytoscape.run_cytoscape(input.pathways, output.session, FRAMEWORK)


# Write a single summary table for all pathways for each dataset
rule summary_table:
    input:
        # Collect all pathways generated for the dataset
        pathways = expand('{out_dir}{sep}{{dataset}}-{algorithm_params}{sep}pathway.txt', out_dir=out_dir, sep=SEP, algorithm_params=algorithms_with_params),
        dataset_file = SEP.join([out_dir, '{dataset}-merged.pickle'])
    output: summary_table = SEP.join([out_dir, '{dataset}-pathway-summary.txt'])
    run:
        # Load the node table from the pickled dataset file
        node_table = Dataset.from_file(input.dataset_file).node_table
        summary_df = summary.summarize_networks(input.pathways, node_table, algorithm_params, algorithms_with_params)
        summary_df.to_csv(output.summary_table, sep='\t', index=False)

# Cluster the output pathways for each dataset
rule ml_analysis:
    input: 
        pathways = expand('{out_dir}{sep}{{dataset}}-{algorithm_params}{sep}pathway.txt', out_dir=out_dir, sep=SEP, algorithm_params=algorithms_with_params)
    output: 
        pca_image = SEP.join([out_dir, '{dataset}-ml', 'pca.png']),
        pca_variance= SEP.join([out_dir, '{dataset}-ml', 'pca-variance.txt']),
        pca_coordinates = SEP.join([out_dir, '{dataset}-ml', 'pca-coordinates.txt']),
        hac_image_vertical = SEP.join([out_dir, '{dataset}-ml', 'hac-vertical.png']),
        hac_clusters_vertical = SEP.join([out_dir, '{dataset}-ml', 'hac-clusters-vertical.txt']),
        hac_image_horizontal = SEP.join([out_dir, '{dataset}-ml', 'hac-horizontal.png']),
        hac_clusters_horizontal = SEP.join([out_dir, '{dataset}-ml', 'hac-clusters-horizontal.txt']),
        pca_kde = SEP.join([out_dir, '{dataset}-ml', 'pca-kde.txt']),
    run: 
        summary_df = ml.summarize_networks(input.pathways)
        ml.hac_vertical(summary_df, output.hac_image_vertical, output.hac_clusters_vertical, **hac_params)
        ml.hac_horizontal(summary_df, output.hac_image_horizontal, output.hac_clusters_horizontal, **hac_params)
        if generate_kde:
            ml.pca(summary_df, output.pca_image, output.pca_variance, output.pca_coordinates, output.pca_kde, **pca_params)
        else: #TODO try to find a different way that doesn't make a dummy file
            ml.pca(summary_df, output.pca_image, output.pca_variance, output.pca_coordinates, **pca_params)
            Path(output.pca_kde).touch()

# Calculated Jaccard similarity between output pathways for each dataset
rule jaccard_similarity:
    input:
        pathways = expand('{out_dir}{sep}{{dataset}}-{algorithm_params}{sep}pathway.txt',
                          out_dir=out_dir, sep=SEP, algorithm_params=algorithms_with_params)
    output:
        jaccard_similarity_matrix = SEP.join([out_dir, '{dataset}-ml', 'jaccard-matrix.txt']),
        jaccard_similarity_heatmap = SEP.join([out_dir, '{dataset}-ml', 'jaccard-heatmap.png'])
    run:
        summary_df = ml.summarize_networks(input.pathways)
        ml.jaccard_similarity_eval(summary_df, output.jaccard_similarity_matrix, output.jaccard_similarity_heatmap)


# Ensemble the output pathways for each dataset
rule ensemble: 
    input:
        pathways = expand('{out_dir}{sep}{{dataset}}-{algorithm_params}{sep}pathway.txt', out_dir=out_dir, sep=SEP, algorithm_params=algorithms_with_params)
    output:
        ensemble_network_file = SEP.join([out_dir,'{dataset}-ml', 'ensemble-pathway.txt'])
    run:
        summary_df = ml.summarize_networks(input.pathways)
        ml.ensemble_network(summary_df, output.ensemble_network_file)

# Returns all pathways for a specific algorithm
def collect_pathways_per_algo(wildcards):
    filtered_algo_params = [algo_param for algo_param in algorithms_with_params if wildcards.algorithm in algo_param]
    return expand('{out_dir}{sep}{{dataset}}-{algorithm_params}{sep}pathway.txt', out_dir=out_dir, sep=SEP, algorithm_params=filtered_algo_params)

# Cluster the output pathways for each dataset per algorithm
rule ml_analysis_aggregate_algo:
    input:
        pathways = collect_pathways_per_algo
    output:
        pca_image = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-pca.png']),
        pca_variance= SEP.join([out_dir, '{dataset}-ml', '{algorithm}-pca-variance.txt']),
        pca_coordinates = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-pca-coordinates.txt']),
        hac_image_vertical = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-hac-vertical.png']),
        hac_clusters_vertical = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-hac-clusters-vertical.txt']),
        hac_image_horizontal = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-hac-horizontal.png']),
        hac_clusters_horizontal = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-hac-clusters-horizontal.txt']),
        pca_kde = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-pca-kde.txt']),
    run:
        summary_df = ml.summarize_networks(input.pathways)
        ml.hac_vertical(summary_df, output.hac_image_vertical, output.hac_clusters_vertical, **hac_params)
        ml.hac_horizontal(summary_df, output.hac_image_horizontal, output.hac_clusters_horizontal, **hac_params)
        if generate_kde:
            ml.pca(summary_df, output.pca_image, output.pca_variance, output.pca_coordinates, output.pca_kde, **pca_params)
        else: #TODO try to find a different way that doesn't make a dummy file
            ml.pca(summary_df, output.pca_image, output.pca_variance, output.pca_coordinates, **pca_params)
            Path(output.pca_kde).touch()

# Ensemble the output pathways for each dataset per algorithm
rule ensemble_per_algo:
    input:
        pathways = collect_pathways_per_algo
    output:
        ensemble_network_file = SEP.join([out_dir,'{dataset}-ml', '{algorithm}-ensemble-pathway.txt'])
    run:
        summary_df = ml.summarize_networks(input.pathways)
        ml.ensemble_network(summary_df, output.ensemble_network_file)

# Calculated Jaccard similarity between output pathways for each dataset per algorithm
rule jaccard_similarity_per_algo:
    input:
         pathways = collect_pathways_per_algo
    output:
        jaccard_similarity_matrix = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-jaccard-matrix.txt']),
        jaccard_similarity_heatmap = SEP.join([out_dir, '{dataset}-ml', '{algorithm}-jaccard-heatmap.png'])
    run:
        summary_df = ml.summarize_networks(input.pathways)
        ml.jaccard_similarity_eval(summary_df, output.jaccard_similarity_matrix, output.jaccard_similarity_heatmap)

# Return the gold standard pickle file for a specific gold standard
def get_gold_standard_pickle_file(wildcards):
    parts = wildcards.dataset_gold_standard_pairs.split('-')
    gs = parts[1]
    return SEP.join([out_dir, f'{gs}-merged.pickle'])

# Returns the dataset corresponding to the gold standard pair
def get_dataset_label(wildcards):
    parts = wildcards.dataset_gold_standard_pairs.split('-')
    dataset = parts[0]
    return dataset

# Return pathway summary file per dataset
def collect_summary_statistics_per_dataset(wildcards):
    dataset_label = get_dataset_label(wildcards)
    return SEP.join([out_dir, f'{dataset_label}-pathway-summary.txt'])

# Returns pca coordinate per dataset
def collect_pca_coordinates_per_dataset(wildcards):
    dataset_label = get_dataset_label(wildcards)
    return expand('{out_dir}{sep}{dataset}-ml{sep}pca-coordinates.txt', out_dir=out_dir, sep=SEP, dataset=dataset_label)


# Run PCA chosen to select the representative from all pathway outputs for a given dataset, 
# then evaluate with precision and recall against the corresponding gold standard
rule evaluation_pca_chosen:
    input: 
        gold_standard_file = get_gold_standard_pickle_file,
        pca_coordinates_file = collect_pca_coordinates_per_dataset,
        pathway_summary_file = collect_summary_statistics_per_dataset
    output: 
        pca_chosen_pr_file = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', "pr-pca-chosen-pathway.txt"]),
        pca_chosen_pr_png = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', "pr-pca-chosen-pathway.png"]),
    run:
        node_table = Evaluation.from_file(input.gold_standard_file).node_table
        pca_chosen_pathway = Evaluation.pca_chosen_pathway(input.pca_coordinates_file, input.pathway_summary_file, out_dir)
        Evaluation.precision_and_recall(pca_chosen_pathway, node_table, algorithms, output.pca_chosen_pr_file, output.pca_chosen_pr_png)

# Returns pca coordinates for a specific algorithm and dataset
def collect_pca_coordinates_per_algo_per_dataset(wildcards):
    dataset_label = get_dataset_label(wildcards)
    return expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-pca-coordinates.txt', out_dir=out_dir, sep=SEP, dataset=dataset_label, algorithm=algorithms_mult_param_combos) #TODO we are using algos with mult param combos, what to do when empty?

# Run PCA chosen to select the representative pathway per algorithm pathway outputs for a given dataset, 
# then evaluate with precision and recall against the corresponding gold standard
rule evaluation_per_algo_pca_chosen:
    input: 
        gold_standard_file = get_gold_standard_pickle_file,
        pca_coordinates_file = collect_pca_coordinates_per_algo_per_dataset,
        pathway_summary_file = collect_summary_statistics_per_dataset
    output: 
        pca_chosen_pr_file = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', "pr-pca-chosen-pathway-per-algorithm.txt"]),
        pca_chosen_pr_png = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', "pr-pca-chosen-pathway-per-algorithm.png"]),
    run:
        node_table = Evaluation.from_file(input.gold_standard_file).node_table
        pca_chosen_pathways = Evaluation.pca_chosen_pathway(input.pca_coordinates_file, input.pathway_summary_file, out_dir)
        Evaluation.precision_and_recall(pca_chosen_pathways, node_table, algorithms, output.pca_chosen_pr_file, output.pca_chosen_pr_png)

# Return the dataset pickle file for a specific dataset
def get_dataset_pickle_file(wildcards):
    dataset_label = get_dataset_label(wildcards)
    return SEP.join([out_dir, f'{dataset_label}-merged.pickle'])

# Returns ensemble file for each dataset
def collect_ensemble_per_dataset(wildcards):
    dataset_label = get_dataset_label(wildcards)
    return expand('{out_dir}{sep}{dataset}-ml{sep}ensemble-pathway.txt', out_dir=out_dir, sep=SEP, dataset=dataset_label)

# Run precision-recall curves for each ensemble pathway within a dataset evaluated against its corresponding gold standard
rule evaluation_ensemble_pr_curve:
    input: 
        gold_standard_file = get_gold_standard_pickle_file,
        dataset_file = get_dataset_pickle_file,
        ensemble_file = collect_ensemble_per_dataset
    output: 
        pr_curve_png = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', 'pr-curve-ensemble-nodes.png']),
        pr_curve_file = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', 'pr-curve-ensemble-nodes.txt']),
    run:
        node_table = Evaluation.from_file(input.gold_standard_file).node_table
        node_ensemble_dict = Evaluation.edge_frequency_node_ensemble(node_table, input.ensemble_file, input.dataset_file)
        Evaluation.precision_recall_curve_node_ensemble(node_ensemble_dict, node_table, output.pr_curve_png, output.pr_curve_file)

# Returns list of algorithm specific ensemble files per dataset
def collect_ensemble_per_algo_per_dataset(wildcards):
    dataset_label = get_dataset_label(wildcards)
    return expand('{out_dir}{sep}{dataset}-ml{sep}{algorithm}-ensemble-pathway.txt', out_dir=out_dir, sep=SEP, dataset=dataset_label, algorithm=algorithms)

# Run precision-recall curves for each algorithm's ensemble pathway within a dataset evaluated against its corresponding gold standard
rule evaluation_per_algo_ensemble_pr_curve:
    input: 
        gold_standard_file = get_gold_standard_pickle_file,
        dataset_file = get_dataset_pickle_file,
        ensemble_files = collect_ensemble_per_algo_per_dataset
    output: 
        pr_curve_png = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', 'pr-curve-ensemble-nodes-per-algorithm.png']),
        pr_curve_file = SEP.join([out_dir, '{dataset_gold_standard_pairs}-eval', 'pr-curve-ensemble-nodes-per-algorithm.txt']),
    run:
        node_table = Evaluation.from_file(input.gold_standard_file).node_table
        node_ensembles_dict = Evaluation.edge_frequency_node_ensemble(node_table, input.ensemble_files, input.dataset_file)
        Evaluation.precision_recall_curve_node_ensemble(node_ensembles_dict, node_table, output.pr_curve_png, output.pr_curve_file)

# Remove the output directory
rule clean:
    shell: f'rm -rf {out_dir}'
