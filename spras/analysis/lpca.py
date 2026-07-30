# Logistic PCA analysis for SPRAS
# Runs LPCA on the binary edge x algorithm matrix produced by summarize_networks.
# Configured through the analysis.lpca block (k, m, cv, transpose).

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from spras.analysis.ml import create_palette
from spras.config.container_schema import ProcessedContainerSettings
from spras.containers import prepare_volume, run_container_and_log

# Published as docker.io/reedcompbio/lpca:v1. Only the suffix is given here;
# the registry prefix is resolved from the container settings.
LPCA_CONTAINER_SUFFIX = 'lpca:v1'
LPCA_WORK_DIR = '/app'


def run_lpca(
    dataframe: pd.DataFrame,
    output_scores: str,
    output_matrix: str,
    k: int = 2,
    m: float = 6,
    cv: bool = False,
    container_settings=None
) -> None:
    """
    Runs Logistic PCA on the binary edge x algorithm matrix built from SPRAS
    algorithm output files.

    @param dataframe: binary dataframe of edge comparison between algorithms from summarize_networks
    @param output_matrix: path to write the binary matrix CSV (used as Docker volume mount)
    @param output_scores: path to write the LPCA PC scores CSV
    @param k: number of principal components (default 2)
    @param m: fixed logisticPCA tuning parameter, used when cv is False
    @param cv: if True, determine m by cross-validation; if False, use the
        fixed m directly (default False)
    @param container_settings: configure the container runtime (Docker or Singularity)

    Note: KDE-based parameter selection (used by PCA) always uses PCA scores, even when LPCA
    is also enabled. KDE integration with LPCA may be added in a future update.
    """
    if not container_settings:
        container_settings = ProcessedContainerSettings()

    # Step 1: build the binary edge x algorithm matrix
    matrix = dataframe
    # Transpose so runs are the observations, mirroring the classic PCA analysis
    matrix = matrix.T
    print(f'LPCA: Matrix shape: {matrix.shape}')

    # Step 2: write the binary matrix for Docker volume mount
    output_dir = Path(output_scores).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    Path(output_matrix).parent.mkdir(parents=True, exist_ok=True)
    matrix_path = output_matrix
    matrix.to_csv(matrix_path)

    # Step 3: mount the matrix and the scores output
    volumes = []
    bind_path, mapped_matrix = prepare_volume(matrix_path, LPCA_WORK_DIR, container_settings)
    volumes.append(bind_path)
    bind_path, mapped_scores = prepare_volume(output_scores, LPCA_WORK_DIR, container_settings)
    volumes.append(bind_path)

    # Step 4: choose m, optionally via cross-validation
    if cv:
        algo_name = Path(output_scores).name.replace('-lpca-scores.csv', '')
        cv_output_path = str(output_dir / f'{algo_name}-lpca_cv_result.csv')
        bind_path, mapped_cv_output = prepare_volume(cv_output_path, LPCA_WORK_DIR, container_settings)
        volumes.append(bind_path)

        print(f'LPCA: Running cross-validation with k={k}...')
        command_cv = ['Rscript', '/app/run_cv.R', mapped_matrix, mapped_cv_output, str(k)]
        run_container_and_log('LPCA-CV', LPCA_CONTAINER_SUFFIX, command_cv, volumes,
                              LPCA_WORK_DIR, None, container_settings)

        if not Path(cv_output_path).exists():
            raise FileNotFoundError(
                f'LPCA: Cross-validation output not found at {cv_output_path}. '
                'Check the LPCA Docker container logs for errors.'
            )
        m_used = pd.read_csv(cv_output_path)['best_m'][0]
        print(f'LPCA: Best m found by CV: {m_used}')
    else:
        m_used = m
        print(f'LPCA: Using fixed m={m_used}')

    # Step 5: run LPCA with the chosen k and m
    print(f'LPCA: Running LPCA with k={k}, m={m_used}...')
    command_lpca = ['Rscript', '/app/run_lpca.R', mapped_matrix, mapped_scores, str(k), str(m_used)]
    run_container_and_log('LPCA', LPCA_CONTAINER_SUFFIX, command_lpca, volumes,
                          LPCA_WORK_DIR, None, container_settings)

    print(f'LPCA: Done! Scores saved to {output_scores}')

def plot_lpca(scores_file: str, output_png: str, output_coord: str, labels: bool = True) -> None:
    """
    Creates a scatterplot of the first two LPCA principal components.
    @param scores_file: path to the LPCA scores CSV file
    @param output_png: path to save the scatterplot PNG
    @param output_coord: path to save the PC coordinates
    @param labels: if True, adds algorithm labels to the plot
    """
    scores = pd.read_csv(scores_file, index_col=0)

    if scores.empty:
        print('LPCA: Scores file is empty, skipping plot.')
        return

    # Extract algorithm names from the index
    column_names = [idx.split('-')[-3] if '-' in idx else idx for idx in scores.index]

    X = scores.values
    fig, ax = plt.subplots(figsize=(10, 8))

    label_color_map = create_palette(column_names)
    sns.scatterplot(x=X[:, 0], y=X[:, 1], hue=column_names, palette=label_color_map, s=70, ax=ax)

    if labels:
        for i, label in enumerate(scores.index):
            ax.annotate(label, (X[i, 0], X[i, 1]), fontsize=6, alpha=0.7)

    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.set_title('Logistic PCA')

    plt.tight_layout()

    # Save PNG
    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_png, dpi=200)
    plt.close()

    # Save coordinates
    coord_df = pd.DataFrame(X, columns=['PC1', 'PC2'], index=scores.index)
    coord_df.to_csv(output_coord)
    print(f'LPCA: Plot saved to {output_png}')
