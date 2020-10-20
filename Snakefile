algorithms = ['pathlinker']
datasets = ['data1']
data_dir = 'input'
out_dir = 'output'

# One rule per reconstruction method initially
# Universal input to PathLinker input
rule prepare_input_pathlinker:
    input: # named arguments for network, sources, targets
    output: # one new file per input file formatted for PathLinker
    shell: # run the preprocessing script for PathLinker

# Run PathLinker
rule reconstruct_pathlinker:
    input: # named arguments for network, sources, targets in PathLinker format
    output: # raw reconstructed pathway in PathLinker format
    shell: # run PathLinker

# PathLinker output to universal output
rule parse_output_pathlinker:
    input: # raw reconstructed pathway
    output: # reconstructed pathway in universal format
    shell: # run the preprocessing script for this particular reconstruction method

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule reconstruct_pathways:
    # Not using arguments yet
    input: expand('{{out_dir}}/{dataset}-{algorithm}-pathway.txt', dataset=datasets, algorithm=algorithms)
