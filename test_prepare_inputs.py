import PRRunner
import shutil
import yaml
import os

config_loc = os.path.join("config","config.yaml")

with open(config_loc) as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
test_file = "test_pickled_dataset.pkl"
PRRunner.merge_input(config["datasets"][0], test_file)
print(PRRunner.get_required_inputs("pathlinker"))
os.makedirs("tmp_output", exist_ok=True) #it is assumed directories will be made upstream
filename_map = {"nodetypes": os.path.join("tmp_output", "nodetypes.txt"),
                "network": os.path.join("tmp_output", "network.txt")}
PRRunner.prepare_inputs("pathlinker",test_file,filename_map)
os.remove(test_file)
shutil.rmtree("tmp_output")
