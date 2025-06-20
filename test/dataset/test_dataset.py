from pathlib import Path

import pandas
import pytest

from spras.dataset import Dataset

FIXTURES_PATH = Path('test', 'dataset', 'fixtures')

class TestDataset:
    def test_not_allow_no_cols(self):
        with pytest.raises(pandas.errors.EmptyDataError):
            Dataset({
                'label': 'empty',
                'edge_files': ['network.txt'],
                'node_files': ['scores.txt', 'nodes.txt'],
                'other_files': [],
                'data_dir': FIXTURES_PATH / 'empty'
            })

    def test_not_allow_edge_weights_oor(self):
        with pytest.raises(ValueError):
            Dataset({
                'label': 'empty',
                'edge_files': ['network.txt'],
                'node_files': ['node-prizes.txt', 'sources.txt', 'targets.txt'],
                'other_files': [],
                'data_dir': FIXTURES_PATH / 'not-in-range'
            })

    def test_normal(self):
        dataset = Dataset({
            'label': 'empty',
            'edge_files': ['network.txt'],
            'node_files': ['node-prizes.txt', 'sources.txt', 'targets.txt'],
            'other_files': [],
            'data_dir': FIXTURES_PATH / 'in-range'
        })

        assert len(dataset.get_interactome()) == 2
