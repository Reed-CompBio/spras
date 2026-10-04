"""Test SPRAS integration; numerical edge cases belong in docker-wrappers/LPCA/test_container.py."""

import shutil
from pathlib import Path
from unittest.mock import Mock

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy.spatial.distance import pdist

from spras.analysis import lpca
from spras.analysis.ml import summarize_networks

INPUT_DIR = Path(__file__).parent / 'input' / 'lpca'
# Existing four-graph fixture, logisticPCA 0.2, k=2, m=4. Distances allow a
# common change of axis orientation, not independent sign changes per graph.
REFERENCE_SCORES = np.array([
    [4.96756989310632, -7.80927209388169],
    [-7.42875819587666, 7.21294742051829],
    [12.7488840407735, 1.711517188498],
    [-11.2979872320273, -5.51380214217161],
])
REFERENCE_DEVIANCE = 91.92536834497237


@pytest.fixture
def outputs(tmp_path):
    return {
        'output_png': tmp_path / 'lpca.png',
        'output_deviance': tmp_path / 'lpca-deviance.txt',
        'output_coord': tmp_path / 'lpca-coordinates.txt',
        'output_matrix': tmp_path / 'lpca-binary-matrix.csv',
    }


@pytest.mark.parametrize('per_algorithm', [False, True], ids=['all_algorithms', 'per_algorithm'])
def test_lpca_container(tmp_path, outputs, per_algorithm):
    algorithms = ['allpairs'] * 4 if per_algorithm else ['allpairs', 'allpairs', 'meo', 'meo']
    paths = []
    for i, algorithm in enumerate(algorithms, start=1):
        # summarize_networks derives run identifiers from parent directories.
        path = tmp_path / 'input graphs' / f'dataset-{algorithm}-params-{i:07d}' / 'pathway.txt'
        path.parent.mkdir(parents=True)
        shutil.copyfile(INPUT_DIR / f'pathway-params-{i}.txt', path)
        paths.append(path)
    networks = summarize_networks(paths)
    lpca.run_lpca(networks, **outputs, m=4, labels=not per_algorithm)

    assert all(path.is_file() for path in outputs.values())
    assert outputs['output_png'].read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    matrix = pd.read_csv(outputs['output_matrix'], index_col='datapoint_labels')
    pd.testing.assert_frame_equal(matrix, networks.T.rename_axis('datapoint_labels'))
    coordinates = pd.read_csv(outputs['output_coord'], sep='\t')
    assert list(coordinates.columns) == ['datapoint_labels', 'PC1', 'PC2']
    assert coordinates['datapoint_labels'].tolist() == list(networks.columns)
    points = coordinates[['PC1', 'PC2']].to_numpy()
    assert points.shape == (4, 2)
    assert np.isfinite(points).all()
    np.testing.assert_allclose(pdist(points), pdist(REFERENCE_SCORES), atol=1e-3, rtol=0)
    summary = dict(line.split(': ', 1)
                   for line in outputs['output_deviance'].read_text().splitlines())
    assert float(summary['components']) == 2
    assert float(summary['m']) == 4
    assert float(summary['percent_deviance_explained']) == pytest.approx(
        REFERENCE_DEVIANCE, abs=1e-3, rel=0)
    assert not list(tmp_path.glob('.lpca-*'))


@pytest.mark.parametrize('labels', [True, False])
def test_plot_lpca(outputs, monkeypatch, labels):
    names = ['001', 'NA', 'dataset-meo-params-CCCCCCC', 'run-four']
    scores = pd.DataFrame(REFERENCE_SCORES, columns=['PC1', 'PC2'], index=names)
    # Mock records calls without moving labels, so we can inspect what our
    # plotting code passes to the label-placement function.
    adjust = Mock()
    # Replace the name used by lpca only for this test. The monkeypatch
    # fixture restores the original function afterward, even on failure.
    monkeypatch.setattr(lpca, 'adjust_text', adjust)
    lpca.plot_lpca(scores, outputs['output_png'], outputs['output_coord'],
                   REFERENCE_DEVIANCE, labels=labels)

    coordinates = pd.read_csv(outputs['output_coord'], sep='\t',
                              dtype={'datapoint_labels': str}, keep_default_na=False)
    assert list(coordinates.columns) == ['datapoint_labels', 'PC1', 'PC2']
    assert coordinates['datapoint_labels'].tolist() == names
    np.testing.assert_allclose(coordinates[['PC1', 'PC2']], REFERENCE_SCORES,
                               atol=1e-8, rtol=0)
    assert outputs['output_png'].read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    if labels:
        adjust.assert_called_once()
        # call_args stores the last call; kwargs contains named arguments.
        ax = adjust.call_args.kwargs['ax']
        assert len(ax.collections) == 1  # Only graph coordinates; no extra plotted points.
        np.testing.assert_allclose(ax.collections[0].get_offsets(), REFERENCE_SCORES)
        assert ax.get_xlabel() == 'PC1'
        assert ax.get_ylabel() == 'PC2'
        assert ax.get_title() == 'Logistic PCA (91.9% deviance explained)'
        # args[0] is the first positional argument: the list of text labels.
        assert [text.get_text() for text in adjust.call_args.args[0]] == names
        assert not plt.fignum_exists(ax.figure.number)
    else:
        adjust.assert_not_called()


def test_container_failure_propagates(tmp_path, outputs, monkeypatch):
    # side_effect raises this error when the mock is called, simulating a
    # failed container without starting Docker. The call is still recorded.
    failure = Mock(side_effect=RuntimeError('container failed'))
    # Replace lpca's imported function; pytest restores it after this test.
    monkeypatch.setattr(lpca, 'run_container_and_log', failure)
    networks = pd.DataFrame(np.eye(3), columns=['a', 'b', 'c'])
    with pytest.raises(RuntimeError, match='container failed'):
        lpca.run_lpca(networks, **outputs)
    failure.assert_called_once()
    # The sixth positional argument is the container helper's output directory.
    assert failure.call_args.args[5] == tmp_path
    assert not outputs['output_png'].exists()
    assert not outputs['output_coord'].exists()
    assert not list(tmp_path.glob('.lpca-*'))
