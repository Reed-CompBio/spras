import PRRunner
import yaml
import DataLoader
import os

config_loc = os.path.join("config","config.yaml")

with open(config_loc) as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
data = DataLoader.DataLoader(config)
test_file = "test_pickled_dataset.pkl"
data.to_file(test_file)
loaded_data = DataLoader.DataLoader.from_file(test_file)
print(PRRunner.get_required_inputs("pathlinker"))
os.makedirs("output", exist_ok=True) #it is assumed directories will be made upstream
PRRunner.prepare_inputs("output/","pathlinker",loaded_data,"data1",{})
os.remove(test_file)
