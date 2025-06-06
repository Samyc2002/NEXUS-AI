import os
import yaml

config_file_path = "E:\\Projects\\NEXUS Main\\NEXUS AI\\config.yaml"

def load_config():
    with open(config_file_path) as config_file:
        config = yaml.safe_load(config_file)
        for key in config.keys():
            os.environ[key] = str(config[key])