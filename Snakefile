# Initially the shell commands do not do anything
# They simply echo the input filename into the expected output file
import os

wildcard_constraints:
    algorithm='\d+'

algorithms = ['pathlinker']
datasets = ['data1']
data_dir = 'input'
out_dir = 'output'

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule reconstruct_pathways:
    # Not using pathway reconstruction method arguments yet
    input: expand('{out_dir}/{dataset}-{algorithm}-pathway.txt', out_dir=out_dir, dataset=datasets, algorithm=algorithms)

# One rule per reconstruction method initially
# Universal input to PathLinker input
rule prepare_input_pathlinker:
    input:
        sources=os.path.join(data_dir, '{dataset}-sources.txt'),
        targets=os.path.join(data_dir, '{dataset}-targets.txt'),
        network=os.path.join(data_dir, '{dataset}-network.txt')
    output:
        sources=os.path.join(out_dir, '{dataset}-{algorithm}-sources.txt'),
        targets=os.path.join(out_dir, '{dataset}-{algorithm}-targets.txt'),
        network=os.path.join(out_dir, '{dataset}-{algorithm}-network.txt')
    # run the preprocessing script for PathLinker
    shell:
        '''
        echo {input.sources} >> {output.sources}
        echo {input.targets} >> {output.targets}
        echo {input.network} >> {output.network}
        '''

# Run PathLinker
rule reconstruct_pathlinker:
    input:
        sources=os.path.join(out_dir, '{dataset}-{algorithm}-sources.txt'),
        targets=os.path.join(out_dir, '{dataset}-{algorithm}-targets.txt'),
        network=os.path.join(out_dir, '{dataset}-{algorithm}-network.txt')
    output: os.path.join(out_dir, '{dataset}-{algorithm}-raw-pathway.txt')
    # run PathLinker
    shell:
        '''
        echo {input.sources} >> {output}
        echo {input.targets} >> {output}
        echo {input.network} >> {output}
        '''

# PathLinker output to universal output
rule parse_output_pathlinker:
    input: os.path.join(out_dir, '{dataset}-{algorithm}-raw-pathway.txt')
    output: os.path.join(out_dir, '{dataset}-{algorithm}-pathway.txt')
    # run the post-processing script for PathLinker
    shell: 'echo {input} >> {output}'
