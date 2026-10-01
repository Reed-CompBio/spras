"""Test LPCA scheduling and reruns using existing graph fixtures, not reconstruction."""

import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from spras.config.config import Config

REPO = Path(__file__).resolve().parents[1]
LPCA_FILES = ('lpca.png', 'lpca-deviance.txt', 'lpca-coordinates.txt', 'lpca-binary-matrix.csv')


@pytest.fixture
def workflow_config(tmp_path):
    raw = {
        'containers': {'registry': {}},
        'immutable_files': False,
        'datasets': [{'label': 'toy', 'data_dir': '.',
                      'node_files': [], 'edge_files': [], 'other_files': []}],
        'algorithms': [
            {'name': 'pathlinker', 'include': True, 'runs': {'test': {'k': [1, 2, 3, 4]}}},
            {'name': 'meo', 'include': True, 'runs': {'test': {'max_path_length': [1, 2]}}},
        ],
        'reconstruction_settings': {'locations': {'reconstruction_dir': 'output'}},
        'analysis': {
            # Disable PCA/HAC explicitly; LPCA does not depend on them.
            'ml': {'include': False},
            'lpca': {'include': True, 'aggregate_per_algorithm': True,
                     'm': 4, 'labels': False},
        },
    }
    parsed = Config(raw)
    logs_dir = tmp_path / 'output' / 'logs'
    logs_dir.mkdir(parents=True)
    # Seed completed reconstruction inputs. Only LPCA and the final-target rule
    # are allowed below, so no reconstruction container or input dataset is needed.
    for algorithm, combinations in parsed.algorithm_params.items():
        for i, params_hash in enumerate(combinations, start=1):
            run = f'{algorithm}-params-{params_hash}'
            pathway_file = tmp_path / 'output' / f'toy-{run}' / 'pathway.txt'
            fixture_file = REPO / 'test/analysis/input/lpca' / f'pathway-params-{i}.txt'
            pathway_file.parent.mkdir()
            shutil.copyfile(fixture_file, pathway_file)
            # The final target requires these logs, but LPCA does not read them.
            parameter_log = logs_dir / f'parameters-{run}.yaml'
            parameter_log.write_text('{}\n', encoding='utf-8')
    dataset_log = logs_dir / 'datasets-toy.yaml'
    dataset_log.write_text('{}\n', encoding='utf-8')
    return raw


def run_workflow(tmp_path, raw, *options):
    config_file = tmp_path / 'config.yaml'
    config_file.write_text(yaml.safe_dump(raw), encoding='utf-8')
    # Run the actual Snakefile in an isolated directory, including its metadata.
    snakefile = REPO / 'Snakefile'
    result = subprocess.run(
        [sys.executable, '-m', 'snakemake', 'all', '--snakefile', str(snakefile),
         '--configfile', str(config_file), '--cores', '1', '--nocolor', *options,
         '--allowed-rules', 'all', 'lpca_analysis_all', 'lpca_analysis_aggregate_algo'],
        cwd=tmp_path, capture_output=True, text=True, timeout=300,
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def lpca_summary(tmp_path, raw):
    # --summary builds the real DAG without executing it and reports each output's
    # status and update plan. It can test scheduling without a running Docker daemon.
    text = run_workflow(tmp_path, raw, '--summary')
    summary_rows = csv.DictReader(text.splitlines(), delimiter='\t')
    lpca_rows = {}
    for row in summary_rows:
        if row['rule'].startswith('lpca_analysis_'):
            output_file = row['output_file'].replace('\\', '/')
            lpca_rows[output_file] = row
    return lpca_rows


def expected_outputs(aggregate):
    prefixes = ['']  # The combined analysis has no algorithm prefix.
    if aggregate:
        prefixes.append('pathlinker-')

    outputs = set()
    for prefix in prefixes:
        for name in LPCA_FILES:
            output_file = f'output/toy-ml/{prefix}{name}'
            outputs.add(output_file)
    return outputs


@pytest.mark.parametrize('include, aggregate', [
    (False, False), (False, True), (True, False), (True, True),
])
def test_lpca_targets(tmp_path, workflow_config, include, aggregate):
    workflow_config['analysis']['lpca'].update(
        include=include, aggregate_per_algorithm=aggregate)
    rows = lpca_summary(tmp_path, workflow_config)
    assert set(rows) == (expected_outputs(aggregate) if include else set())
    # The two-run algorithm contributes to the combined fit but is not eligible
    # for its own fit. The fixture explicitly sets analysis.ml.include=False.
    assert not any('meo-lpca' in name for name in rows)


def test_lpca_workflow_reruns(tmp_path, workflow_config):
    """Requires Docker and the LPCA image; never forces a rerun."""
    # Reuse the same directory so Snakemake retains the first run's metadata.
    # Create the outputs at m=4, then change only m to verify automatic reruns.
    for m in (4, 6):
        workflow_config['analysis']['lpca']['m'] = m
        before = lpca_summary(tmp_path, workflow_config)
        assert set(before) == expected_outputs(True)
        assert all(row['plan'] == 'update pending' for row in before.values())
        if m == 6:
            # These outputs already exist, so the reason must be changed params.
            assert all(row['status'] == 'params changed' for row in before.values())

        # Execute normally, then check that another invocation needs no work.
        run_workflow(tmp_path, workflow_config)
        after = lpca_summary(tmp_path, workflow_config)
        assert set(after) == expected_outputs(True)
        assert all(row['plan'] == 'no update' for row in after.values())

        # Combined: four PathLinker and two MEO graphs. Separate: PathLinker only.
        output_dir = tmp_path / 'output' / 'toy-ml'
        for prefix, count in [('', 6), ('pathlinker-', 4)]:
            coordinates_file = output_dir / f'{prefix}lpca-coordinates.txt'
            matrix_file = output_dir / f'{prefix}lpca-binary-matrix.csv'
            deviance_file = output_dir / f'{prefix}lpca-deviance.txt'
            coordinates = pd.read_csv(coordinates_file, sep='\t')
            matrix = pd.read_csv(matrix_file)
            assert len(coordinates) == count
            assert coordinates['datapoint_labels'].tolist() == matrix['datapoint_labels'].tolist()
            if prefix:
                assert coordinates['datapoint_labels'].str.contains('-pathlinker-', regex=False).all()

            # Verify the actual fit used the new m, not just that it was scheduled.
            summary = {}
            for line in deviance_file.read_text().splitlines():
                key, value = line.split(': ', 1)
                summary[key] = value
            assert float(summary['m']) == m

    # Changing labels should schedule an update; no extra fit is needed to check this.
    workflow_config['analysis']['lpca']['labels'] = True
    rows = lpca_summary(tmp_path, workflow_config)
    assert set(rows) == expected_outputs(True)
    assert all(row['status'] == 'params changed' for row in rows.values())
    # Restore the executed setting so the next check isolates a missing output.
    workflow_config['analysis']['lpca']['labels'] = False

    # A missing fit summary must schedule its producer even when the plot exists.
    missing_output = 'output/toy-ml/lpca-deviance.txt'
    missing_file = tmp_path / missing_output
    missing_file.unlink()
    rows = lpca_summary(tmp_path, workflow_config)
    assert rows[missing_output]['status'] == 'missing'
    assert rows[missing_output]['plan'] == 'update pending'
