"""Fixed-m, two-component LPCA of pathway graphs from one or more algorithms."""

from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from adjustText import adjust_text

from spras.analysis.ml import DPI, create_palette
from spras.config.container_schema import ProcessedContainerSettings
from spras.containers import prepare_volume, run_container_and_log
from spras.util import make_required_dirs

# The registry prefix is resolved from the container settings.
LPCA_CONTAINER_SUFFIX = 'lpca:v1'
LPCA_WORK_DIR = '/app'


def run_lpca(
    dataframe: pd.DataFrame,
    output_png: str | PathLike,
    output_deviance: str | PathLike,
    output_coord: str | PathLike,
    output_matrix: str | PathLike,
    k: int = 2,
    m: float = 6,
    labels: bool = True,
    container_settings: ProcessedContainerSettings | None = None,
) -> None:
    """Fit and plot the graphs in the edges-by-runs summarize_networks dataframe.

    The caller selects runs from one algorithm or across algorithms. Containerized R validates
    the inputs and numerical fit. Python writes the input matrix, calls R, and
    produces a plot and tab-separated coordinates with one row per input graph.
    The deviance summary is written by R; its raw scores are temporary.
    """
    if container_settings is None:
        container_settings = ProcessedContainerSettings()
    for path in (output_png, output_deviance, output_coord, output_matrix):
        make_required_dirs(path)
    output_dir = Path(output_png).parent
    matrix = dataframe.T
    matrix.to_csv(output_matrix, index_label='datapoint_labels')
    print(f'LPCA: Matrix shape: {matrix.shape}; k={k}, m={m}')

    with TemporaryDirectory(prefix='.lpca-', dir=output_dir) as temp_dir:
        scores_file = Path(temp_dir) / 'scores.csv'
        matrix_volume, mapped_matrix = prepare_volume(output_matrix, LPCA_WORK_DIR, container_settings)
        scores_volume, mapped_scores = prepare_volume(scores_file, LPCA_WORK_DIR, container_settings)
        deviance_volume, mapped_deviance = prepare_volume(output_deviance, LPCA_WORK_DIR, container_settings)
        volumes = [matrix_volume, scores_volume, deviance_volume]
        command = ['Rscript', '/app/run_lpca.R', mapped_matrix, mapped_scores,
                   str(k), str(m), mapped_deviance]
        run_container_and_log('LPCA', LPCA_CONTAINER_SUFFIX, command, volumes,
                              LPCA_WORK_DIR, output_dir, container_settings)

        # Preserve identifiers and require one pair of scores per input graph.
        scores = pd.read_csv(scores_file, index_col='datapoint_labels',
                             dtype={'datapoint_labels': str}, keep_default_na=False)
        if (list(scores.columns) != ['PC1', 'PC2'] or
                scores.index.tolist() != matrix.index.tolist()):
            raise ValueError('LPCA scores must contain PC1/PC2 and the input run labels in order.')

    with open(output_deviance) as summary_file:
        summary = dict(line.strip().split(': ', 1) for line in summary_file)
    percent_deviance = float(summary['percent_deviance_explained'])
    plot_lpca(scores, output_png, output_coord, percent_deviance, labels=labels)


def plot_lpca(
    scores: pd.DataFrame,
    output_png: str | PathLike,
    output_coord: str | PathLike,
    percent_deviance: float,
    labels: bool = True,
) -> None:
    """Plot run scores and save their coordinates; output directories must exist."""
    scores.rename_axis('datapoint_labels').round(8).to_csv(output_coord, sep='\t')
    column_names = [name.split('-')[-3] if name.count('-') >= 2 else name
                    for name in scores.index]
    points = scores.to_numpy()
    fig, ax = plt.subplots(figsize=(10, 7))
    try:
        sns.scatterplot(x=points[:, 0], y=points[:, 1], hue=column_names,
                        palette=create_palette(column_names), s=70, ax=ax)
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_title(f'Logistic PCA ({percent_deviance:.1f}% deviance explained)')
        fig.tight_layout()
        if labels:
            texts = [ax.text(x, y, name, size=10)
                     for (x, y), name in zip(points, scores.index, strict=True)]
            adjust_text(texts, ax=ax, force_points=(5.0, 5.0),
                        arrowprops=dict(arrowstyle='->', color='black'))
        fig.savefig(output_png, dpi=DPI)
    finally:
        plt.close(fig)
