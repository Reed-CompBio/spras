import filecmp
import os
import shutil
from pathlib import Path

import yaml

from src import runner

OUTDIR = "test/PrepareInputs/output/"
EXPDIR = "test/PrepareInputs/expected/"
class TestPrepareInputs:
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUTDIR).mkdir(parents=True, exist_ok=True)

    def test_prepare_inputs_networks(self):
        config_loc = os.path.join("config", "config.yaml")

        with open(config_loc) as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)
        test_file = "test/PrepareInputs/output/test_pickled_dataset.pkl"

        for dataset in config["datasets"]:
            runner.merge_input(dataset, test_file)

            # Test PathLinker
            filename_map = {"nodetypes": os.path.join("test","PrepareInputs", "output", "pl-nodetypes.txt"),
                            "network": os.path.join("test","PrepareInputs", "output", "pl-network.txt")}
            runner.prepare_inputs("pathlinker", test_file, filename_map)
            assert filecmp.cmp(OUTDIR +'pl-network.txt', EXPDIR + 'pl-network-expected.txt')

            # Test OmicsIntegrator1
            filename_map = {"prizes": os.path.join("test","PrepareInputs", "output", "oi1-prizes.txt"),
                            "edges": os.path.join("test","PrepareInputs", "output", "oi1-network.txt")}
            runner.prepare_inputs("omicsintegrator1", test_file, filename_map)
            assert filecmp.cmp(OUTDIR +'oi1-network.txt', EXPDIR + 'oi1-network-expected.txt')

            # Test OmicsIntegrator2
            filename_map = {"prizes": os.path.join("test","PrepareInputs", "output", "oi2-prizes.txt"),
                            "edges": os.path.join("test","PrepareInputs", "output", "oi2-network.txt")}
            runner.prepare_inputs("omicsintegrator2", test_file, filename_map)
            assert filecmp.cmp(OUTDIR +'oi2-network.txt', EXPDIR + 'oi2-network-expected.txt')

            # Test MEO
            filename_map = {"sources": os.path.join("test","PrepareInputs", "output", "meo-sources.txt"),
                            "targets": os.path.join("test","PrepareInputs", "output", "meo-targets.txt"),
                            "edges": os.path.join("test","PrepareInputs", "output", "meo-edges.txt")}
            runner.prepare_inputs("meo", test_file, filename_map)
            assert filecmp.cmp(OUTDIR +'meo-edges.txt', EXPDIR + 'meo-edges-expected.txt')

            # Test MCF
            filename_map = {"sources": os.path.join("test","PrepareInputs", "output", "mcf-sources.txt"),
                            "targets": os.path.join("test","PrepareInputs", "output", "mcf-targets.txt"),
                            "edges": os.path.join("test","PrepareInputs", "output", "mcf-edges.txt")}
            runner.prepare_inputs("mincostflow", test_file, filename_map)
            assert filecmp.cmp(OUTDIR +'mcf-edges.txt', EXPDIR + 'mcf-edges-expected.txt')

            # Test AllPairs
            filename_map = {"nodetypes": os.path.join("test","PrepareInputs", "output", "ap-nodetypes.txt"),
                            "network": os.path.join("test","PrepareInputs", "output", "ap-network.txt")}
            runner.prepare_inputs("allpairs", test_file, filename_map)
            assert filecmp.cmp(OUTDIR +'ap-network.txt', EXPDIR + 'ap-network-expected.txt')

            # Test Domino
            filename_map = {"network": os.path.join("test","PrepareInputs", "output", "d-network.txt"),
                            "active_genes": os.path.join("test","PrepareInputs", "output", "d-active_genes.txt")}
            runner.prepare_inputs("domino", test_file, filename_map)
            assert filecmp.cmp(OUTDIR +'d-network.txt', EXPDIR + 'd-network-expected.txt')

            break # only run dataset 0
