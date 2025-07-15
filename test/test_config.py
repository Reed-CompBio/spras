import pickle

import numpy as np
import pytest

import spras.config.config as config
from spras.config.container_schema import DEFAULT_CONTAINER_PREFIX
from spras.config.schema import DEFAULT_HASH_LENGTH

filler_dataset_data: dict[str, str | list[str]] = {
    "data_dir": "fake",
    "edge_files": [],
    "other_files": [],
    "node_files": []
}

# Set up a dummy config for testing. For now, only include things that MUST exist in the dict
# in order for the config init to complete. To test particular parts of the config initialization,
# individual values of the dict can be changed and the whole initialization can be re-run.
def get_test_config():
    test_raw_config = {
        "containers": {
            "framework": "singularity",
            "registry": {
                "base_url": "docker.io",
                "owner": "reedcompbio",
            },
        },
        "hash_length": 7,
        "reconstruction_settings": {
            "locations": {
                "reconstruction_dir": "my_dir"
            }
        },
        "datasets": [{
            "label": "alg1",
            "data_dir": "fake",
            "edge_files": [],
            "other_files": [],
            "node_files": []
        }, {
            "label": "alg2",
            "data_dir": "faux",
            "edge_files": [],
            "other_files": [],
            "node_files": []
        }],
        "gold_standards": [{
            "label": "gs1",
            "dataset_labels": [],
            "node_files": [],
            "data_dir": "gs-fake"
        }],
        "algorithms": [
            # Since there is algorithm validation,
            # we are (mostly) forced to use real algorithm parameters here.
            # To make this more readable, we make the 'test names' the run names.
            # TODO: we don't have a test for combinations of strings anymore. This seems to be fine,
            # but it would be nice to have once we introduce an algorithm that takes more than 1 string parameter.
            {
                "name": "omicsintegrator2",
                "include": True,
                "runs": {
                    "strings": {"dummyMode": ["terminals", "others"], "b": 1},
                    # spacing in np.linspace is on purpose
                    "singleton_string_np_linspace": {"dummyMode": "terminals", "b": "np.linspace(0,    5,2)"},
                    "str_array_np_logspace": {"test": ["others", "all"], "g": "np.logspace(1,1)"}
                }
            },
            {
                "name": "meo",
                "include": True,
                "runs": {
                    "numbersAndBool": {"max_path_length": 1, "rand_restarts": [float(2.0), 3], "local_search": True},
                    "numbersAndBools": {"max_path_length": 1, "rand_restarts": [float(2.0), 3], "local_search": [True, False]},
                    "boolArrTest": {"local_search": [True, False], "max_path_length": "range(1, 3)"}
                }
            },
            {
                "name": "mincostflow",
                "include": True,
                "runs": {
                    "int64artifact": {"flow": "np.arange(5,6)", "capacity": [2, 3]}
                }
            },
        ],
        "analysis": {
            "summary": {
                "include": False
            },
            "ml": {
                "include": False,
                "aggregate_per_algorithm": False
            },
            "cytoscape": {
                "include": False
            },
            "evaluation": {
                "include": False,
                 "aggregate_per_algorithm": False
            },
        },
    }

    return test_raw_config

def value_test_util(name: str, configurations: list):
    assert name in config.config.algorithm_params, f"{name} isn't a present algorithm configuration!"

    keys = config.config.algorithm_params[name]
    values = [config.config.algorithm_params[name][key] for key in keys]

    # https://stackoverflow.com/a/50486270/7589775
    # Note: We use pickle as we also compare dictionaries in these two sets - some kind of consistent total ordering
    # is required for the tests to consistently pass when comparing them to `configurations`.
    set_values = set(tuple(sorted(d.items())) for d in sorted(values, key=lambda x: pickle.dumps(x, protocol=3)))
    set_configurations = set(tuple(sorted(d.items())) for d in sorted(configurations, key=lambda x: pickle.dumps(x, protocol=3)))

    if set_values != set_configurations:
        print(f'Got: {set_values}')
        print(f'Expected: {set_configurations}')
        assert set_values == set_configurations

class TestConfig:
    """
    Tests various parts of the configuration mechanism
    """
    def test_config_hash_length(self):
        # Initialize the configuration
        test_config = get_test_config()
        config.init_global(test_config)
        assert (config.config.hash_length == 7)

        test_config.pop("hash_length", None)
        config.init_global(test_config)
        assert (config.config.hash_length == DEFAULT_HASH_LENGTH)

        # Initialize the configuration
        test_config["hash_length"] = "12"
        config.init_global(test_config)
        assert (config.config.hash_length == 12)

    def test_config_container_framework_normalization(self):
        # Test singularity
        test_config = get_test_config()

        test_config["containers"]["framework"] = "singularity"
        config.init_global(test_config)
        assert (config.config.container_settings.framework == "singularity")

        # Test singularity with capitalization
        test_config["containers"]["framework"] = "Singularity"
        config.init_global(test_config)
        assert (config.config.container_settings.framework == "singularity")

        # Test docker
        test_config["containers"]["framework"] = "docker"
        config.init_global(test_config)
        assert (config.config.container_settings.framework == "docker")

        # Test docker with capitalization
        test_config["containers"]["framework"] = "Docker"
        config.init_global(test_config)
        assert (config.config.container_settings.framework == "docker")

        # Test unknown framework
        test_config["containers"]["framework"] = "badFramework"
        with pytest.raises(ValueError):
            config.init_global(test_config)

    def test_config_container_registry(self):
        test_config = get_test_config()
        test_config["containers"]["registry"]["base_url"] = "docker.io"
        test_config["containers"]["registry"]["owner"] = "reedcompbio"
        config.init_global(test_config)
        assert (config.config.container_settings.prefix == "docker.io/reedcompbio")

        test_config["containers"]["registry"]["base_url"] = "another.repo"
        test_config["containers"]["registry"]["owner"] = "different-owner"
        config.init_global(test_config)
        assert (config.config.container_settings.prefix == "another.repo/different-owner")

        test_config["containers"]["registry"]["base_url"] = ""
        test_config["containers"]["registry"]["owner"] = ""
        config.init_global(test_config)
        assert (config.config.container_settings.prefix == DEFAULT_CONTAINER_PREFIX)

    def test_error_dataset_label(self):
        test_config = get_test_config()
        error_test_dicts = [{"label": "test$"}, {"label": "@test'"}, {"label": "[test]"}, {"label": "test-test"},
                            {"label": "✉"}]

        for test_dict in error_test_dicts:
            test_config["datasets"] = [test_dict]
            with pytest.raises(ValueError):  # raises error if any chars other than letters, numbers, or underscores are in dataset label
                config.init_global(test_config)

    def test_correct_dataset_label(self):
        test_config = get_test_config()
        correct_test_dicts = [{"label": "test"},  {"label": "123"}, {"label": "test123"}, {"label": "123test"}, {"label": "_"},
                              {"label": "test_test"}, {"label": "_test"}, {"label": "test_"}]
        correct_test_dicts = [dict(list(d.items()) + list(filler_dataset_data.items())) for d in correct_test_dicts]

        for test_dict in correct_test_dicts:
            test_config["datasets"] = [test_dict]
            config.init_global(test_config)  # no error should be raised

    def test_error_gs_label(self):
        test_config = get_test_config()
        error_labels = ["test$", "@test'"]

        for test_label in error_labels:
            test_config["gold_standards"][0]["label"] = test_label
            with pytest.raises(ValueError):  # raises error if any chars other than letters, numbers, or underscores are in gs label
                config.init_global(test_config)

    def test_error_gs_dataset_mismatch(self):
        test_config = get_test_config()
        test_config["gold_standards"] = [{"label": "gs1", "dataset_labels": ["mismatch"]}]

        with pytest.raises(ValueError):
            config.init_global(test_config)

    def test_config_values(self):
        test_config = get_test_config()
        config.init_global(test_config)

        value_test_util('strings', [{'test': "str1", 'test2': "str2"}, {'test': 'str1', 'test2': 'str3'}])
        value_test_util('numbersAndBools', [{'a': 1, 'b': float(2.0), 'c': 4, 'd': 5.6, 'f': False}, {'a': 1, 'b': 3, 'c': 4, 'd': 5.6, 'f': False}])

        value_test_util('singleton_int64_with_array', [{'test': 1, 'test2': 2}, {'test': 1, 'test2': 3}])
        value_test_util('singleton_string_np_linspace', [{'test': "str1", 'test2': 5.0}, {'test': "str1", 'test2': 0.0}])
        value_test_util('str_array_np_logspace', [{'test': "a", 'test2': 10}] * 10 + [{'test': "b", 'test2': 10}] * 10)

        value_test_util('int64artifact', [{'test': 5, 'test2': 2}, {'test': 5, 'test2': 3}])

        value_test_util('boolArrTest', [{'flags': True, 'range': 1}, {'flags': False, 'range': 2},
                                     {'flags': False, 'range': 1}, {'flags': True, 'range': 2}])

    @pytest.mark.parametrize("ml_include, eval_include, expected_ml, expected_eval", [
        (True, True, True, True),
        (True, False, True, False),
        (False, True, False, False),
        (False, False, False, False)
    ])
    def test_eval_ml_coupling(self, ml_include, eval_include, expected_ml, expected_eval):
        test_config = get_test_config()
        test_config["analysis"]["ml"]["include"] = ml_include
        test_config["analysis"]["evaluation"]["include"] = eval_include
        config.init_global(test_config)

        assert config.config.analysis_include_ml == expected_ml
        assert config.config.analysis_include_evaluation == expected_eval

    @pytest.mark.parametrize("ml_include, ml_agg_include, expected_ml, expected_ml_agg", [
        (True, True, True, True),
        (True, False, True, False),
        (False, True, False, False),
        (False, False, False, False)
    ])
    def test_ml_agg_algo_coupling(self, ml_include, ml_agg_include, expected_ml, expected_ml_agg):
        test_config = get_test_config()
        test_config["analysis"]["ml"]["include"] = ml_include
        test_config["analysis"]["ml"]["aggregate_per_algorithm"] = ml_agg_include
        config.init_global(test_config)

        assert config.config.analysis_include_ml == expected_ml
        assert config.config.analysis_include_ml_aggregate_algo == expected_ml_agg

    @pytest.mark.parametrize("eval_include, agg_algo, expected_eval, expected_agg_algo", [
        (True, True, True, True),
        (True, False, True, False),
        (False, True, False, False),
        (False, False, False, False),
    ])
    def test_eval_agg_algo_coupling(self, eval_include, agg_algo, expected_eval, expected_agg_algo):
        test_config = get_test_config()
        test_config["analysis"]["ml"]["include"] = True
        test_config["analysis"]["ml"]["aggregate_per_algorithm"] = True

        test_config["analysis"]["evaluation"]["include"] = eval_include
        test_config["analysis"]["evaluation"]["aggregate_per_algorithm"] = agg_algo

        config.init_global(test_config)

        assert config.config.analysis_include_evaluation == expected_eval
        assert config.config.analysis_include_evaluation_aggregate_algo == expected_agg_algo

    @pytest.mark.parametrize("ml_include, ml_agg, eval_include, eval_agg, expected_ml, expected_ml_agg, expected_eval, expected_eval_agg", [
        (False, True,  True,  True,  False, False, False, False),
        (True,  False, True,  True,  True,  False, True,  False),
        (False, False, True,  True,  False, False, False, False),
        (True,  True,  True,  True,  True,  True,  True,  True),
        (True,  False, False, False, True,  False, False, False),
    ])
    def test_eval_ml_agg_algo_coupling(self, ml_include, ml_agg, eval_include, eval_agg, expected_ml, expected_ml_agg,
                                       expected_eval, expected_eval_agg):
        # the value of ml include and ml aggregate_per_algorithm can affect the value of evaluation include and
        # evaluation aggregate_per_algorithm
        test_config = get_test_config()

        test_config["analysis"]["ml"]["include"] = ml_include
        test_config["analysis"]["ml"]["aggregate_per_algorithm"] = ml_agg
        test_config["analysis"]["evaluation"]["include"] = eval_include
        test_config["analysis"]["evaluation"]["aggregate_per_algorithm"] = eval_agg

        config.init_global(test_config)

        assert config.config.analysis_include_ml == expected_ml
        assert config.config.analysis_include_ml_aggregate_algo == expected_ml_agg
        assert config.config.analysis_include_evaluation == expected_eval
        assert config.config.analysis_include_evaluation_aggregate_algo == expected_eval_agg
