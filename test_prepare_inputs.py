import PRRunner
import shutil
import yaml
import os

config_loc = os.path.join("config","config.yaml")

with open(config_loc) as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
test_file = "test_pickled_dataset.pkl"

for i in [0,1]:
    PRRunner.merge_input(config["datasets"][i], test_file)
    os.makedirs("tmp_output", exist_ok=True) #it is assumed directories will be made upstream

#Test pathlinker
    filename_map = {"nodetypes": os.path.join("tmp_output", "pl-nodetypes.txt"),
                    "network": os.path.join("tmp_output", "pl-network.txt")}
    PRRunner.prepare_inputs("pathlinker",test_file,filename_map)

#Test OmicsIntegrator1
    filename_map = {"prizes": os.path.join("tmp_output", "oi1-prizes.txt"),
                    "edges": os.path.join("tmp_output", "oi1-network.txt")}
    PRRunner.prepare_inputs("omicsintegrator1",test_file,filename_map)

#Test OmicsIntegrator2
    filename_map = {"prizes": os.path.join("tmp_output", "oi2-prizes.txt"),
                    "edges": os.path.join("tmp_output", "oi2-network.txt")}
    PRRunner.prepare_inputs("omicsintegrator2",test_file,filename_map)

    os.remove(test_file)
    shutil.rmtree("tmp_output")
