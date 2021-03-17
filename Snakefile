# Initially the shell commands do not do anything
# They simply echo the input filename into the expected output file
import itertools as it
import os
import PRRunner

configfile: "config/config.yaml"
wildcard_constraints:
    algorithm='\w+'

algorithm_params = dict()
datasets = []
data_dir = ""
out_dir = ""


def parse_config_file():
    global datasets
    global data_dir
    global out_dir
    global algorithm_params

    # Parse dataset information
    # Need to work more on input file naming to make less strict assumptions
    # about the filename structure
    datasets = config["data"]["datasets"]
    data_dir = config["data"]["data_dir"]
    out_dir  = config["data"]["out_dir"]

    # Parse algorithm information
    # Each algorithm's parameters are provided as a list of dictionaries
    # Defaults are handled in the Python function or class that wraps
    # running that algorithm
    # Keys in the parameter dictionary are strings
    for alg in config["algorithms"]:
        # Each set of runs should be 1 level down in the config file
        for params in alg["params"]:
            all_runs = []
            if params == "include":
                if alg["params"][params]:
                    # This is trusting that "include" is always first
                    algorithm_params[alg["name"]] = []
                    continue
                else:
                    break
            # We create a the product of all param combinations for each run
            param_name_list = []
            if alg["params"][params] is not None:
                for p in alg["params"][params]:
                    param_name_list.append(p)
                    all_runs.append(eval(str(alg["params"][params][p])))
            run_list_tuples = list(it.product(*all_runs))
            param_name_tuple = tuple(param_name_list)
            for r in run_list_tuples:
                run_dict = dict(zip(param_name_tuple,r))
                algorithm_params[alg["name"]].append(run_dict)

parse_config_file()
algorithms = list(algorithm_params.keys())
pathlinker_params = algorithm_params['pathlinker'] # Temporary

# This would be part of our Python package
required_inputs = {
    'pathlinker': ['sources', 'targets', 'network'],
    'pcsf': ['nodes', 'network'],
    'bowtiebuilder': ['nodes', 'network']
    }

# Eventually we'd store these values in a config file
run_options = {}
run_options["augment"] = False
run_options["parameter-advise"] = False

# Used to be generate_param_counts(algorithm_params)
# Now, make a dictionary of (key,Runner object) pairs, where
#   KEY is algorithm name plus param count index.
#   RUNNER OBJECT is one of PathLinker, BowTieBuilder, or PCSF instantiated classes with params.
# Returns this dictionary; keys are used later for algorithms_with_params
def get_runners(algorithm_params):
    algorithm_runners = {}
    for algorithm, param_list in algorithm_params.items():

        #algorithm_param_counts[algorithm] = len(param_list)
        ## make a dictionary of all runners.
        i = 0
        for param in param_list:
            ## QUESTION: should the Runner object get inputs for the algs and set those?
            ## Right now itis inconsistent: we pass it specific parameters, but NOT input/output
            ## files. It just pulls inputdir and outputdir, but not specific filenames.
            ## These seem to be created in the reconstruct rule, but I wonder if it should be
            ## specified here.
            param_dict = {'name':algorithm,'inputdir':data_dir,'outputdir':out_dir,'params':param}
            key = '{}-{}'.format(algorithm,i)
            print(algorithm)
            ## This should be able to be dynamically specified.
            ## For now, instantiate the object according to the algorithm name.
            algorithm_runners[key] = globals()[algorithm](param_dict)
            # if algorithm == 'pathlinker':
            #     algorithm_runners[key] = pathlinker(param_dict)
            # elif algorithm == 'bowtiebuilder':
            #     algorithm_runners[key] = bowtiebuilder(param_dict)
            # elif algorithm == 'pcsf':
            #     algorithm_runners[key] = pcsf(param_dict)
            # else:
            #     sys.exit('{} not specified. add to the IF/ELIF statement in get_runners() for now.'.format(algorithm))
            i+=1
    return algorithm_runners

algorithm_runners = get_runners(algorithm_params)
algorithms_with_params = list(algorithm_runners.keys())
#print(algorithms_with_params)
print(algorithm_runners)
# sys.exit()

# Get the parameter dictionary for the specified
# algorithm and index
def reconstruction_params(algorithm, index_string):
    index = int(index_string.replace('params', ''))
    return algorithm_params[algorithm][index]

# Determine which input files are needed based on the
# pathway reconstruction algorithm
# May no longer need a function for this, but keep it because
# the final implementation may be more complex than a dictionary
def reconstruction_inputs(algorithm):
    return required_inputs[algorithm]

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
        final_input = expand('{out_dir}{sep}augmented-pathway-{dataset}-{algorithm}-{params}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms, params=pathlinker_params)
    elif run_options["parameter-advise"]:
        #not a great name
        final_input = expand('{out_dir}{sep}advised-pathway-{dataset}-{algorithm}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms)
    else:
        # Use 'params<index>' in the filename instead of describing each of the parameters and its value
        final_input = expand('{out_dir}{sep}pathway-{dataset}-{algorithm_params}.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm_params=algorithms_with_params)
        # Create log files for the parameter indices
        final_input.extend(expand('{out_dir}{sep}parameters-{algorithm}.txt', out_dir=out_dir, sep=os.sep, algorithm=algorithms))
    return final_input

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule reconstruct_pathways:
    # Look for a more elegant way to use the OS-specific separator
    # Probably do not want filenames to dictate which parameters to sweep over,
    # consider alternative implementations
    # input: expand('{out_dir}{sep}{dataset}-{algorithm}-{params}-pathway.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms, params=pathlinker_params)
    input: make_final_input
    # Test only the prepare_input_pathlinker rule
    # If using os.path.join use it everywhere because having some / and some \
    # separators can cause the pattern matching to fail
    #input: os.path.join(out_dir, 'data1-pathlinker-network.txt')

# Universal input to pathway reconstruction-specific input
# Currently makes a strict assumption about the filename of the input files
rule prepare_input:
    input: os.path.join(data_dir, '{dataset}-{type}.txt')
    output: os.path.join(out_dir, '{dataset}-{algorithm}-{type}.txt')
    # run the preprocessing script for this algorithm
    # With Git Bash on Windows multiline strings are not executed properly
    # https://carpentries-incubator.github.io/workflows-snakemake/07-resources/index.html
    # (No longer applicable for this command, but a good reminder)
    shell:
        '''
        echo Original file: {input} >> {output}
        '''

# See https://stackoverflow.com/questions/46714560/snakemake-how-do-i-use-a-function-that-takes-in-a-wildcard-and-returns-a-value
# for why the lambda function is required
# Run PathLinker or other pathway reconstruction algorithm
rule reconstruct:
    input: lambda wildcards: expand(os.path.join(out_dir, '{{dataset}}-{{algorithm}}-{type}.txt'), type=reconstruction_inputs(algorithm=wildcards.algorithm))
    output: os.path.join(out_dir, 'raw-pathway-{dataset}-{algorithm}-{params}.txt')
    # chain.from_iterable trick from https://stackoverflow.com/questions/3471999/how-do-i-merge-two-lists-into-a-single-list
    run:
        print(f"cur algo: {wildcards.algorithm}")
        params = reconstruction_params(wildcards.algorithm, wildcards.params)
        # Add the input files
        params.update(dict(zip(reconstruction_inputs(wildcards.algorithm), *{input})))
        # Add the output file
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
