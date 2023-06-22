import os
import shutil

import yaml

from src import runner

config_loc = os.path.join("config", "config.yaml")

with open(config_loc) as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
test_file = "test_pickled_dataset.pkl"

for dataset in config["datasets"]:
    runner.merge_input(dataset, test_file)
    os.makedirs("tmp_output", exist_ok=True) #it is assumed directories will be made upstream

    # Test PathLinker
    filename_map = {"nodetypes": os.path.join("tmp_output", "pl-nodetypes.txt"),
                    "network": os.path.join("tmp_output", "pl-network.txt")}
    runner.prepare_inputs("pathlinker", test_file, filename_map)

    # Test OmicsIntegrator1
    filename_map = {"prizes": os.path.join("tmp_output", "oi1-prizes.txt"),
                    "edges": os.path.join("tmp_output", "oi1-network.txt")}
    runner.prepare_inputs("omicsintegrator1", test_file, filename_map)

    # Test OmicsIntegrator2
    filename_map = {"prizes": os.path.join("tmp_output", "oi2-prizes.txt"),
                    "edges": os.path.join("tmp_output", "oi2-network.txt")}
    runner.prepare_inputs("omicsintegrator2", test_file, filename_map)

    # Test MEO
    filename_map = {"sources": os.path.join("tmp_output", "meo-sources.txt"),
                    "targets": os.path.join("tmp_output", "meo-targets.txt"),
                    "edges": os.path.join("tmp_output", "meo-edges.txt")}
    runner.prepare_inputs("meo", test_file, filename_map)

    os.remove(test_file)
    shutil.rmtree("tmp_output")
