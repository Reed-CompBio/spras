import copy
import pickle
from typing import Iterable

import pytest
from pydantic import BaseModel

import spras.config.config as config
from spras.config.container_schema import DEFAULT_CONTAINER_PREFIX
from spras.config.schema import DEFAULT_HASH_LENGTH
from spras.meo import MEOParams
from spras.mincostflow import MinCostFlowParams
from spras.omicsintegrator2 import DummyMode, OmicsIntegrator2Params

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
            "label": "gs_fake",
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
                    "strings": {"dummy_mode": ["terminals", "others"], "b": 3},
                    # spacing in np.linspace is on purpose
                    "singleton_string_np_linspace": {"dummy_mode": "terminals", "b": "np.linspace(0,    5,2,)"},
                    "str_array_np_logspace": {"dummy_mode": ["others", "all"], "g": "np.logspace(1,1)"}
                }
            },
            {
                "name": "meo",
                "include": True,
                "runs": {
                    "numbersAndBoolsDuplicate": {"max_path_length": 1, "rand_restarts": [float(2.0), 3], "local_search": [True, False]},
                    "numbersAndBool": {"max_path_length": 2, "rand_restarts": [float(2.0), 3], "local_search": [True]},
                    "numbersAndBools": {"max_path_length": 1, "rand_restarts": [float(2.0), 3], "local_search": [True, False]},
                    "boolArrTest": {"local_search": [True, False], "max_path_length": "range(1, 3)"}
                }
            },
            {
                "name": "mincostflow",
                "include": True,
                "runs": {
                    "int64artifact": {"flow": "np.arange(5, 7)", "capacity": [2, 3]}
                }
            },
        ],
        "analysis": {
            "summary": {
                "include": False
            },
            "ml": {
                "include": False,
                "aggregate_per_algorithm": False,
            },
            "cytoscape": {
                "include": False
            },
            "evaluation": {
                "include": False,
                "aggregate_per_algorithm": False
            },
            "attribution": {
                "include": False
            },
        },
    }

    return test_raw_config

def value_test_util(alg: str, run_name: str, param_type: type[BaseModel], configurations: Iterable[BaseModel]):
    """
    Utility test function to be able to test against certain named runs
    under algorithms. This is, unfortunately, a very holistic function that depends
    on the current state of how config parsing is.
    """
    assert alg in config.config.algorithm_params, f"{alg} isn't a present algorithm name!"
    runs = config.config.algorithm_params[alg]
    # Filter using the internal _spras_run_name key.
    runs = {hash: params for hash, params in runs.items() if params["_spras_run_name"] == run_name}

    # We copy values so we don't mutate it
    values: list[dict] = copy.deepcopy(list(runs.values()))
    for value in values:
        # then, remove the internal key for easy comparison.
        del value["_spras_run_name"]

    # Since configurations is a bunch of objects, we need to turn those into dictionaries
    # and exclude their defaults.
    new_configurations = [config.model_dump(exclude_defaults=True) for config in configurations]

    # Same for values, but we reserialize them first
    values = [param_type.model_validate(value).model_dump(exclude_defaults=True) for value in values]

    # Now, we need to also remove any dynamic values from values and configurations
    # (_time and seeded values)
    for value in values:
        value.pop("_time", None)
        value.pop("seed", None)
    for configuration in new_configurations:
        configuration.pop("_time", None)
        configuration.pop("seed", None)

    # https://stackoverflow.com/a/50486270/7589775
    # Note: We use pickle as we also compare dictionaries in these two sets - some kind of consistent total ordering
    # is required for the tests to consistently pass when comparing them to `configurations`.
    final_values = sorted(tuple(sorted(d.items())) for d in sorted(values, key=lambda x: pickle.dumps(x, protocol=3)))
    final_configurations = sorted(tuple(sorted(d.items())) for d in sorted(new_configurations, key=lambda x: pickle.dumps(x, protocol=3)))

    if final_values != final_configurations:
        print(f'Got: {final_values}')
        print(f'Expected: {final_configurations}')
        assert final_values == final_configurations

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

        value_test_util('omicsintegrator2', 'strings', OmicsIntegrator2Params, [
            OmicsIntegrator2Params(dummy_mode=DummyMode.terminals, b=3),
            OmicsIntegrator2Params(dummy_mode=DummyMode.others, b=3)
        ])

        value_test_util('omicsintegrator2', 'singleton_string_np_linspace', OmicsIntegrator2Params, [
            OmicsIntegrator2Params(dummy_mode=DummyMode.terminals, b=5.0),
            OmicsIntegrator2Params(dummy_mode=DummyMode.terminals, b=0.0)
        ])

        value_test_util('omicsintegrator2', 'str_array_np_logspace', OmicsIntegrator2Params, [
            # While these both repeat 50 times, parameter hash makes sure to not duplicate the work.
            # This serves as a test to make sure _time isn't inserted during parameter combinations.
            OmicsIntegrator2Params(dummy_mode=DummyMode.others, g=10), OmicsIntegrator2Params(dummy_mode=DummyMode.all, g=10)
        ])

        value_test_util('meo', 'numbersAndBools', MEOParams, [
            MEOParams(max_path_length=1, rand_restarts=2, local_search=False),
            MEOParams(max_path_length=1, rand_restarts=2, local_search=True),
            MEOParams(max_path_length=1, rand_restarts=3, local_search=False),
            MEOParams(max_path_length=1, rand_restarts=3, local_search=True),
        ])

        # Encoding this behavior: run names are not passed into the parameter hash,
        # and thus won't duplicate runs.
        value_test_util('meo', 'numbersAndBoolsDuplicate', MEOParams, [])

        value_test_util('meo', 'numbersAndBool', MEOParams, [
            MEOParams(max_path_length=2, rand_restarts=2, local_search=True),
            MEOParams(max_path_length=2, rand_restarts=3, local_search=True),
        ])

        value_test_util('mincostflow', 'int64artifact', MinCostFlowParams, [
            MinCostFlowParams(flow=5, capacity=2),
            MinCostFlowParams(flow=5, capacity=3),
            MinCostFlowParams(flow=6, capacity=2),
            MinCostFlowParams(flow=6, capacity=3)
        ])

        value_test_util('meo', 'boolArrTest', MEOParams, [
            MEOParams(local_search=True, max_path_length=1),
            MEOParams(local_search=True, max_path_length=2),
            MEOParams(local_search=False, max_path_length=1),
            MEOParams(local_search=False, max_path_length=2)
        ])

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

    @pytest.mark.parametrize("eval_include, kde, expected_eval, expected_kde", [
        (True, True, True, True),
        (True, False, True, True),
        (False, True, False, True),
        (False, False, False, False),
    ])
    def test_eval_kde_coupling(self, eval_include, kde, expected_eval, expected_kde):
        test_config = get_test_config()
        test_config["analysis"]["ml"]["include"] = True
        # dealing with other coupling issue
        test_config["analysis"]["summary"]["include"] = True

        test_config["analysis"]["ml"]["kde"] = kde
        test_config["analysis"]["evaluation"]["include"] = eval_include

        config.init_global(test_config)

        assert config.config.analysis_include_evaluation == expected_eval
        assert config.config.pca_params["kde"] == expected_kde

    @pytest.mark.parametrize("eval_include, summary_include, expected_eval, expected_summary", [
        (True, True, True, True),
        (True, False, True, True),
        (False, True, False, True),
        (False, False, False, False),
    ])
    def test_eval_summary_coupling(self, eval_include, summary_include, expected_eval, expected_summary):
        test_config = get_test_config()
        # dealing with other coupling issue
        test_config["analysis"]["ml"]["include"] = True
        test_config["analysis"]["ml"]["kde"] = True

        test_config["analysis"]["summary"]["include"] = summary_include
        test_config["analysis"]["evaluation"]["include"] = eval_include

        config.init_global(test_config)

        assert config.config.analysis_include_evaluation == expected_eval
        assert config.config.analysis_include_summary == expected_summary

