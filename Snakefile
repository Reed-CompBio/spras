# Initially the shell commands do not do anything
# They simply echo the input filename into the expected output file
import os

wildcard_constraints:
    algorithm='\w+'

algorithms = ['pathlinker']
pathlinker_params = ['k5', 'k10']
datasets = ['data1']
data_dir = 'input'
out_dir = 'output'

# A rule to define all the expected outputs from all pathway reconstruction
# algorithms run on all datasets for all arguments
rule reconstruct_pathways:
    # Look for a more elegant way to use the OS-specific separator
    # Probably do not want filenames to dictate which parameters to sweep over,
    # consider alternative implementations
    input: expand('{out_dir}{sep}{dataset}-{algorithm}-{params}-pathway.txt', out_dir=out_dir, sep=os.sep, dataset=datasets, algorithm=algorithms, params=pathlinker_params)
    # Test only the prepare_input_pathlinker rule
    # If using os.path.join use it everywhere because having some / and some \
    # separators can cause the pattern matching to fail
    #input: os.path.join(out_dir, 'data1-pathlinker-network.txt')

# One rule per reconstruction method initially
# Universal input to PathLinker input
rule prepare_input_pathlinker:
    input:
        sources=os.path.join(data_dir, '{dataset}-sources.txt'),
        targets=os.path.join(data_dir, '{dataset}-targets.txt'),
        network=os.path.join(data_dir, '{dataset}-network.txt')
    # No need to use {algorithm} here instead of 'pathlinker' if this is a
    # PathLinker rule instead of a generic prepare input rule
    output:
        sources=os.path.join(out_dir, '{dataset}-{algorithm}-sources.txt'),
        targets=os.path.join(out_dir, '{dataset}-{algorithm}-targets.txt'),
        network=os.path.join(out_dir, '{dataset}-{algorithm}-network.txt')
    # run the preprocessing script for PathLinker
    # With Git Bash on Windows multiline strings are not executed properly
    # https://carpentries-incubator.github.io/workflows-snakemake/07-resources/index.html
    shell:
        '''
        echo {input.sources} >> {output.sources} && echo {input.targets} >> {output.targets} && echo {input.network} >> {output.network}
        '''

# Run PathLinker
rule reconstruct_pathlinker:
    input:
        sources=os.path.join(out_dir, '{dataset}-{algorithm}-sources.txt'),
        targets=os.path.join(out_dir, '{dataset}-{algorithm}-targets.txt'),
        network=os.path.join(out_dir, '{dataset}-{algorithm}-network.txt')
    output: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-raw-pathway.txt')
    # run PathLinker
    shell: 'echo {input.sources} >> {output} && echo {input.targets} >> {output} && echo {input.network} >> {output} && echo Params: {wildcards.params} >> {output}'

# PathLinker output to universal output
rule parse_output_pathlinker:
    input: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-raw-pathway.txt')
    output: os.path.join(out_dir, '{dataset}-{algorithm}-{params}-pathway.txt')
    # run the post-processing script for PathLinker
    shell: 'echo {input} >> {output}'

# Remove the output directory
rule clean:
    shell: f'rm -rf {out_dir}'
