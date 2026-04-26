from pathlib import Path

import pandas
import pytest

from spras.config.dataset import DatasetSchema
from spras.dataset import Dataset

FIXTURES_PATH = Path('test', 'dataset', 'fixtures')

class TestDataset:
    def test_not_allow_no_cols(self):
        with pytest.raises(pandas.errors.EmptyDataError):
            Dataset(DatasetSchema(
                label='empty',
                edge_files=['network.txt'],
                node_files=['sources.txt', 'node-prizes.txt'],
                other_files=[],
                data_dir=FIXTURES_PATH / 'empty'
            ))

    def test_not_allow_no_cols_headers(self):
        with pytest.raises(pandas.errors.EmptyDataError):
            Dataset(DatasetSchema(
                label='empty_headers',
                edge_files=['network.txt'],
                node_files=['sources.txt', 'node-prizes.txt'],
                other_files=[],
                data_dir=FIXTURES_PATH / 'empty-headers'
            ))

    def test_dataless(self):
        with pytest.raises(pandas.errors.EmptyDataError):
            Dataset(DatasetSchema(
                label='dataless',
                edge_files=['network.txt'],
                node_files=['sources.txt', 'node-prizes.txt'],
                other_files=[],
                data_dir=FIXTURES_PATH / 'dataless'
            ))

    def test_empty_network(self):
        with pytest.raises(pandas.errors.EmptyDataError):
            Dataset(DatasetSchema(
                label='empty_network',
                edge_files=['network.txt'],
                node_files=['sources.txt', 'node-prizes.txt'],
                other_files=[],
                data_dir=FIXTURES_PATH / 'empty-network'
            ))

    def test_standard(self):
        dataset = Dataset(DatasetSchema(
            label='empty',
            edge_files=['network.txt'],
            node_files=['node-prizes.txt', 'sources.txt', 'targets.txt'],
            other_files=[],
            data_dir=FIXTURES_PATH / 'standard'
        ))

        assert len(dataset.get_interactome()) == 2
