# One rule? Or one per reconstruction method?
rule prepare_input:
    input: # named arguments for network, sources, targets and the reconstruction method
    output: # one new file per input file formatted for the reconstruction method
    shell: # run the preprocessing script for this particular reconstruction method
