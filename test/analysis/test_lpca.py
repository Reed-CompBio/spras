from pathlib import Path

import pandas as pd

import spras.config.config as config
from spras.analysis.lpca import plot_lpca, run_lpca
from spras.analysis.ml import summarize_networks

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test/analysis/')
OUT_DIR = TEST_DIR / 'output'

INPUT_FILES = [
    'test/analysis/input/lpca/pathway-params-1.txt',
    'test/analysis/input/lpca/pathway-params-2.txt',
    'test/analysis/input/lpca/pathway-params-3.txt',
    'test/analysis/input/lpca/pathway-params-4.txt',
]

class TestLpca:
    """
    Run Logistic PCA (LPCA) analysis tests
    """
    @classmethod
    def setup_class(cls):
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    def test_lpca_output_exists(self):
        """Test that LPCA produces an output scores file"""
        out_path = OUT_DIR / 'lpca-scores.csv'
        matrix_path = OUT_DIR / 'lpca-binary-matrix.csv'
        out_path.unlink(missing_ok=True)

        summary_df = summarize_networks(INPUT_FILES)
        run_lpca(
            dataframe=summary_df,
            output_scores=str(out_path),
            output_matrix=str(matrix_path),
            k=2,
            m=4,
            cv=False,
        )

        assert out_path.exists(), "LPCA scores file was not created"

    def test_lpca_output_shape(self):
        """Test that LPCA scores have shape (runs x k)"""
        out_path = OUT_DIR / 'lpca-scores-shape.csv'
        matrix_path = OUT_DIR / 'lpca-binary-matrix-shape.csv'
        out_path.unlink(missing_ok=True)

        summary_df = summarize_networks(INPUT_FILES)
        run_lpca(
            dataframe=summary_df,
            output_scores=str(out_path),
            output_matrix=str(matrix_path),
            k=2,
            m=4,
            cv=False,
        )

        scores = pd.read_csv(out_path, index_col=0)
        assert scores.shape[1] == 2, f"Expected 2 PC columns, got {scores.shape[1]}"
        assert scores.shape[0] == len(INPUT_FILES), \
            f"Expected {len(INPUT_FILES)} rows, got {scores.shape[0]}"

    def test_lpca_plot_output(self):
        """Test that LPCA plot and coordinates files are created"""
        scores_path = OUT_DIR / 'lpca-scores-plot.csv'
        matrix_path = OUT_DIR / 'lpca-binary-matrix-plot.csv'
        png_path = OUT_DIR / 'lpca-plot.png'
        coord_path = OUT_DIR / 'lpca-coordinates.txt'

        summary_df = summarize_networks(INPUT_FILES)
        run_lpca(
            dataframe=summary_df,
            output_scores=str(scores_path),
            output_matrix=str(matrix_path),
            k=2,
            m=4,
            cv=False,
        )
        plot_lpca(str(scores_path), str(png_path), str(coord_path))

        assert png_path.exists(), "LPCA plot PNG was not created"
        assert coord_path.exists(), "LPCA coordinates file was not created"

    def test_lpca_known_output(self):
        """Test that LPCA produces the expected scores for known inputs.

        Compared in absolute value because LPCA components, like PCA, are only
        defined up to a sign (an axis can flip without changing the result).
        """
        out_path = OUT_DIR / 'lpca-scores-known.csv'
        matrix_path = OUT_DIR / 'lpca-binary-matrix-known.csv'
        out_path.unlink(missing_ok=True)

        summary_df = summarize_networks(INPUT_FILES)
        run_lpca(
            dataframe=summary_df,
            output_scores=str(out_path),
            output_matrix=str(matrix_path),
            k=2,
            m=4,
            cv=False,
        )

        scores = pd.read_csv(out_path, index_col=0)

        expected = pd.DataFrame({
            'V1': [4.96756989310632, -7.42875819587666, 12.7488840407735, -11.2979872320273],
            'V2': [-7.80927209388169, 7.21294742051829, 1.711517188498, -5.51380214217161],
        })

        assert scores.shape == expected.shape, \
            f"Expected shape {expected.shape}, got {scores.shape}"

        # Compare in absolute value to stay robust to sign flips (sign non-identifiability)
        pd.testing.assert_frame_equal(
            scores.reset_index(drop=True).abs(),
            expected.abs(),
            check_dtype=False,
            atol=1e-4,
        )
