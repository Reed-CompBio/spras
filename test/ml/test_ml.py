import filecmp
from pathlib import Path

import pandas as pd

import src.analysis.ml as ml

INPUT_DIR = 'test/ml/input/'
OUT_DIR = 'test/ml/output/'
EXPECT_DIR = 'test/ml/expected/'


class TestML:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def test_summarize_networks(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 's1/s1.txt', INPUT_DIR + 's2/s2.txt', INPUT_DIR + 's3/s3.txt',
                                           INPUT_DIR + 'longName/longName.txt', INPUT_DIR + 'longName2/longName2.txt',
                                           INPUT_DIR + 'empty/empty.txt', INPUT_DIR + 'spaces/spaces.txt'])
        dataframe.to_csv(OUT_DIR + 'dataframe.csv')
        assert filecmp.cmp(OUT_DIR + 'dataframe.csv', EXPECT_DIR + 'expected_df.csv')

    def test_pca(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 's1/s1.txt', INPUT_DIR + 's2/s2.txt', INPUT_DIR + 's3/s3.txt'])
        ml.pca(dataframe, OUT_DIR + 'pca/pca.png', OUT_DIR + 'pca/pca-components.txt',
               OUT_DIR + 'pca/pca-coordinates.csv')
        coord = pd.read_table(OUT_DIR + 'pca/pca-coordinates.csv')
        coord = coord.round(5)  # round values to 5 digits to account for numeric differences across machines
        expected = pd.read_table(EXPECT_DIR + 'expected_coords.csv')
        expected = expected.round(5)

        assert coord.equals(expected)

    def test_hac(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 's1/s1.txt', INPUT_DIR + 's2/s2.txt', INPUT_DIR + 's3/s3.txt'])
        ml.hac(dataframe, OUT_DIR + 'hac/hac.png', OUT_DIR + 'hac/hac-clusters.txt')

        assert filecmp.cmp(OUT_DIR + 'hac/hac-clusters.txt', EXPECT_DIR + 'expected_clusters.txt')
