from pathlib import Path

import pandas
import pytest
import numpy as np

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
    
    # 372 is a PR, but for the relevant comment, see
    # https://github.com/Reed-CompBio/spras/pull/372/files#r2291953612.
    # Note that the input-nodes file has more tabs than the original fixture.
    def test_372(self):
        dataset = Dataset({
            'label': 'toy-372',
            'edge_files': ['input-interactome.txt'],
            'node_files': ['input-nodes.txt'],
            'data_dir': FIXTURES_PATH / 'toy-372',
            'other_files': []
        })

        node_table = dataset.node_table
        assert node_table is not None

        assert node_table[node_table[Dataset.NODE_ID] == 'C'].iloc[0]['prize'] == 5.7
        assert node_table[node_table[Dataset.NODE_ID] == 'C'].iloc[0]['active'] == True

        assert np.isnan(node_table[node_table[Dataset.NODE_ID] == 'C'].iloc[0]['sources'])
        assert node_table[node_table[Dataset.NODE_ID] == 'C'].iloc[0]['targets'] == True
