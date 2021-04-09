import PRRunner
import yaml
import DataLoader
import os

config_loc = os.path.join("config","config.yaml")
config = {}

with open(config_loc) as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
data = DataLoader.DataLoader(config)
print(PRRunner.get_required_inputs("pathlinker"))
os.makedirs("output", exist_ok=True) #it is assumed directories will be made upstream
PRRunner.prepare_inputs("output/","pathlinker",data,"data1",{})
