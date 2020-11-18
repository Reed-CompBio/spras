# Initially the shell commands do not do anything
# They simply echo the input filename into the expected output file
import itertools as it
import os

wildcard_constraints:
    algorithm='\w+'

algorithms = ['pathlinker']
algorithm_params = {
    'pathlinker': ['k5', 'k10'], # Eventually this would be a list of dictionaries
    'pcsf': ['beta0', 'beta1', 'beta2']
    }
pathlinker_params = algorithm_params['pathlinker'] # Temporary

datasets = ['data1']
data_dir = 'input'
out_dir = 'output'

# This would be part of our Python package
required_inputs = {
    'pathlinker': ['sources', 'targets', 'network'],
    'pcsf': ['nodes', 'network']
    }

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
#print(algorithm_param_counts)
algorithms_with_params = [f'{algorithm}-params{index}' for algorithm, count in algorithm_param_counts.items() for index in range(count)]
#print(algorithms_with_params)

# Get the parameter dictionary (currently string) for the specified
# algorithm and index
def reconstruction_params(algorithm, index_string):
    index = int(index_string.replace('params', ''))
    return algorithm_params[algorithm][index]

# Determine which input files are needed based on the
# pathway reconstruction algorithm
# May no longer need a function for this, but keep it because
# the final implmentation may be more complex than a dictionary
def reconstruction_inputs(algorithm):
    return required_inputs[algorithm]

# Choose the final input for reconstruct_pathways based on which options are being run
# Right now this is a static run_options dictionary but would eventually
# be done with the config file
def make_final_input(wildcards):
    # Right now this lets us do ppa or augmentation, but not both. 
    # An easy solution would be to make a seperate rule for doing both, but 
    # if we add more things to do after the fact that will get
    # out of control pretty quickly. Steps run in parallel won't have this problem, just ones
    # whose inputs depend on each other. 
    # Currently, this will not re-generate all of the individual pathways
    # when augmenting or advising
    # Changes to the parameter handling may have broken the augment and advising options
    if run_options["augment"]:
        final_input = expand('{out_dir}{sep}{dataset}-{algorithm}-{params}-pathway-augmented.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms, params=pathlinker_params)
    elif run_options["parameter-advise"]:
        #not a great name
        final_input = expand('{out_dir}{sep}{dataset}-{algorithm}-pathway-advised.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms)
    else:
        # Use 'params<index>' in the filename instead of describing each of the parameters and its value
        final_input = expand('{out_dir}{sep}{dataset}-{algorithm_params}-pathway.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm_params=algorithms_with_params)
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

# One rule per reconstruction method initially, need to generalize
# Universal input to pathway-reconstruction specific input
rule prepare_input_pathlinker:
    input:
        sources=os.path.join(data_dir, '{dataset}-sources.txt'),
        targets=os.path.join(data_dir, '{dataset}-targets.txt'),
        network=os.path.join(data_dir, '{dataset}-network.txt')
    output:
        # Hard code pathlinker instead of {algorithm} to eliminate ambigutiy about how to prepare the network
        sources=os.path.join(out_dir, '{dataset}-pathlinker-sources.txt'),
        targets=os.path.join(out_dir, '{dataset}-pathlinker-targets.txt'),
        network=os.path.join(out_dir, '{dataset}-pathlinker-network.txt')
    # run the preprocessing script for this algorithm
    # With Git Bash on Windows multiline strings are not executed properly
    # https://carpentries-incubator.github.io/workflows-snakemake/07-resources/index.html
    shell:
        '''
        echo {input.sources} >> {output.sources} && echo {input.targets} >> {output.targets} && echo {input.network} >> {output.network}
        '''

# Can delete this once the rule is generalized to work for all algorithms
rule prepare_input_pcsf:
    input:
        nodes=os.path.join(data_dir, '{dataset}-nodes.txt'),
        network=os.path.join(data_dir, '{dataset}-network.txt')
    output:
        nodes=os.path.join(out_dir, '{dataset}-pcsf-nodes.txt'),
        network=os.path.join(out_dir, '{dataset}-pcsf-network.txt')
    shell:
        '''
        echo {input.nodes} >> {output.nodes} && echo {input.network} >> {output.network}
        '''

# See https://stackoverflow.com/questions/46714560/snakemake-how-do-i-use-a-function-that-takes-in-a-wildcard-and-returns-a-value
# for why the lambda function is required
# Run PathLinker or other pathway reconstruction algorithm
rule reconstruct:
    input: lambda wildcards: expand(os.path.join(out_dir, '{{dataset}}-{{algorithm}}-{type}.txt'), type=reconstruction_inputs(algorithm=wildcards.algorithm))
    output: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-raw-pathway.txt')
    # chain.from_iterable trick from https://stackoverflow.com/questions/3471999/how-do-i-merge-two-lists-into-a-single-list
    run:
        input_args = ['--' + arg for arg in reconstruction_inputs(wildcards.algorithm)]
        input_args = list(it.chain.from_iterable(zip(input_args, *{input})))
        params = reconstruction_params(wildcards.algorithm, wildcards.params)
        # Write the command to a file instead of running it because this
        # functionality has not been implemented
        shell('''
            echo python command --algorithm {wildcards.algorithm} {input_args} --output {output} >> {output} && echo Parameters: {params} >> {output}
        ''')

# Original pathway reconstruction output to universal output
rule parse_output:
    input: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-raw-pathway.txt')
    output: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-pathway.txt')
    # run the post-processing script
    shell: 'echo {wildcards.algorithm} {input} >> {output}'

# Pathway Augmentation
rule augment_pathway:
    input: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-pathway.txt')
    output: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-pathway-augmented.txt')
    shell: 'echo {input} >> {output}'

# Pathway Parameter Advising
rule parameter_advise:
    input: expand('{out_dir}{sep}{dataset}-{algorithm}-{params}-pathway.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms, params=pathlinker_params)
    output: os.path.join(out_dir, '{dataset}-{algorithm}-pathway-advised.txt')
    shell: 'echo {input} >> {output}'

# Remove the output directory
rule clean:
    shell: f'rm -rf {out_dir}'
