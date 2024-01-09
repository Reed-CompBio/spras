import pytest

import spras.config as config


# Set up a dummy config for testing. For now, only include things that MUST exist in the dict
# in order for the config init to complete. To test particular parts of the config initialization,
# individual values of the dict can be changed and the whole initialization can be re-run.
def get_test_config():
    test_raw_config = {
        "container_framework": "singularity",
        "container_registry": {
            "base_url": "docker.io",
            "owner": "reedcompbio",
        },
        "hash_length": 7,
        "reconstruction_settings": {
            "locations": {
                "reconstruction_dir": "my_dir"
            }
        },
        "datasets": [{"label":"alg1"}, {"label":"alg2"}],
        "algorithms": [{"params": ["param2", "param2"]}],
        "analysis": {
            "summary": {
                "include": False
            },
            "ml": {
                "include": False
            },
            "graphspace": {
                "include": False
            },
            "cytoscape": {
                "include": False
            },
        },
    }

    return test_raw_config

class TestConfig:
    """
    Tests various parts of the configuration mechanism
    """
    def test_config_hash_length(self):
        # Initialize the configuration
        test_config = get_test_config()
        config.init_global(test_config)
        assert (config.config.hash_length == 7)

        test_config["hash_length"] = ""
        config.init_global(test_config)
        assert (config.config.hash_length == config.DEFAULT_HASH_LENGTH)

        # Initialize the configuration
        test_config["hash_length"] = "12"
        config.init_global(test_config)
        assert (config.config.hash_length == 12)

    def test_config_container_framework_normalization(self):
        # Test singularity
        test_config = get_test_config()

        test_config["container_framework"] = "singularity"
        config.init_global(test_config)
        assert (config.config.container_framework == "singularity")

        # Test singularity with capitalization
        test_config["container_framework"] = "Singularity"
        config.init_global(test_config)
        assert (config.config.container_framework == "singularity")

        # Test docker
        test_config["container_framework"] = "docker"
        config.init_global(test_config)
        assert (config.config.container_framework == "docker")

        # Test docker with capitalization
        test_config["container_framework"] = "Docker"
        config.init_global(test_config)
        assert (config.config.container_framework == "docker")

        # Test unknown framework
        test_config["container_framework"] = "badFramework"
        with pytest.raises(ValueError):
            config.init_global(test_config)

    def test_config_container_registry(self):
        test_config = get_test_config()
        test_config["container_registry"]["base_url"] = "docker.io"
        test_config["container_registry"]["owner"] = "reedcompbio"
        config.init_global(test_config)
        assert (config.config.container_prefix == "docker.io/reedcompbio")

        test_config["container_registry"]["base_url"] = "another.repo"
        test_config["container_registry"]["owner"] = "different-owner"
        config.init_global(test_config)
        assert (config.config.container_prefix == "another.repo/different-owner")

        test_config["container_registry"]["base_url"] = ""
        test_config["container_registry"]["owner"] = ""
        config.init_global(test_config)
        assert (config.config.container_prefix == config.DEFAULT_CONTAINER_PREFIX)



