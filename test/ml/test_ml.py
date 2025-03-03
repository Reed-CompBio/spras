import filecmp
from pathlib import Path

import pandas as pd
import pytest

import spras.analysis.ml as ml

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
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-s1/s1.txt', INPUT_DIR + 'test-data-s2/s2.txt', INPUT_DIR + 'test-data-s3/s3.txt',
                                           INPUT_DIR + 'test-data-longName/longName.txt', INPUT_DIR + 'test-data-longName2/longName2.txt',
                                           INPUT_DIR + 'test-data-empty/empty.txt', INPUT_DIR + 'test-data-spaces/spaces.txt', INPUT_DIR + 'test-data-mixed-direction/mixed-direction.txt'])
        dataframe.to_csv(OUT_DIR + 'dataframe.csv')
        assert filecmp.cmp(OUT_DIR + 'dataframe.csv', EXPECT_DIR + 'expected-dataframe.csv', shallow=False)

    def test_summarize_networks_less_values(self):
        with pytest.raises(ValueError):
            ml.summarize_networks([INPUT_DIR + 'test-data-unexpected-amount-of-values/less.txt'])

    def test_summarize_networks_more_values(self):
        with pytest.raises(ValueError):
            ml.summarize_networks([INPUT_DIR + 'test-data-unexpected-amount-of-values/more.txt'])

    def test_summarize_networks_empty_line(self):
        with pytest.raises(ValueError):
            ml.summarize_networks([INPUT_DIR + 'test-data-empty-line/emptyLine.txt'])

    def test_summarize_networks_wrong_direction(self):
        with pytest.raises(ValueError):
            ml.summarize_networks([INPUT_DIR + 'test-data-wrong-direction/wrong-direction.txt'])

    def test_empty(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-empty/empty.txt'])
        with pytest.raises(ValueError):  # raises error if empty dataframe is used for post processing
            ml.pca(dataframe, OUT_DIR + 'pca-empty.png', OUT_DIR + 'pca-empty-variance.txt',
               OUT_DIR + 'pca-empty-coordinates.tsv')
        with pytest.raises(ValueError):
            ml.hac_horizontal(dataframe, OUT_DIR + 'hac-empty-horizontal.png', OUT_DIR + 'hac-empty-clusters-horizontal.txt')
        with pytest.raises(ValueError):
            ml.hac_vertical(dataframe, OUT_DIR + 'hac-empty-vertical.png', OUT_DIR + 'hac-empty-clusters-vertical.txt')

    def test_single_line(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-empty/empty.txt'])
        with pytest.raises(ValueError):  # raises error if single line in file s.t. single row in dataframe is used for post processing
            ml.pca(dataframe, OUT_DIR + 'pca-single-line.png', OUT_DIR + 'pca-single-line-variance.txt',
               OUT_DIR + 'pca-single-line-coordinates.tsv')
        with pytest.raises(ValueError):
            ml.hac_horizontal(dataframe, OUT_DIR + 'hac-single-line-horizontal.png', OUT_DIR + 'hac-single-line-clusters-horizontal.txt')
        with pytest.raises(ValueError):
            ml.hac_vertical(dataframe, OUT_DIR + 'hac-single-line-vertical.png', OUT_DIR + 'hac-single-line-clusters-vertical.txt')

    def test_pca(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-s1/s1.txt', INPUT_DIR + 'test-data-s2/s2.txt', INPUT_DIR + 'test-data-s3/s3.txt'])
        ml.pca(dataframe, OUT_DIR + 'pca.png', OUT_DIR + 'pca-variance.txt',
               OUT_DIR + 'pca-coordinates.tsv')
        coord = pd.read_table(OUT_DIR + 'pca-coordinates.tsv')
        coord = coord.round(5)  # round values to 5 digits to account for numeric differences across machines
        expected = pd.read_table(EXPECT_DIR + 'expected-pca-coordinates.tsv')
        expected = expected.round(5)

        assert coord.equals(expected)

    def test_pca_robustness(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-s1/s1.txt', INPUT_DIR + 'test-data-s2/s2.txt', INPUT_DIR + 'test-data-s3/s3.txt'])
        expected = pd.read_table(EXPECT_DIR + 'expected-pca-coordinates.tsv')
        expected = expected.round(5)
        for _ in range(5):
            dataframe_shuffled = dataframe.sample(frac=1, axis=1)  # permute the columns
            ml.pca(dataframe_shuffled, OUT_DIR + 'pca-shuffled-columns.png', OUT_DIR + 'pca-shuffled-columns-variance.txt',
                OUT_DIR + 'pca-shuffled-columns-coordinates.tsv')
            coord = pd.read_table(OUT_DIR + 'pca-shuffled-columns-coordinates.tsv')
            coord = coord.round(5)  # round values to 5 digits to account for numeric differences across machines
            coord.sort_values(by='algorithm', ignore_index=True, inplace=True)

            assert coord.equals(expected)

        for _ in range(5):
            dataframe_shuffled = dataframe.sample(frac=1, axis=0)  # permute the rows
            ml.pca(dataframe_shuffled, OUT_DIR + 'pca-shuffled-rows.png', OUT_DIR + 'pca-shuffled-rows-variance.txt',
                    OUT_DIR + 'pca-shuffled-rows-coordinates.tsv')
            coord = pd.read_table(OUT_DIR + 'pca-shuffled-rows-coordinates.tsv')
            coord = coord.round(5)  # round values to 5 digits to account for numeric differences across machines
            coord.sort_values(by='algorithm', ignore_index=True, inplace=True)

            assert coord.equals(expected)

    def test_hac_horizontal(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-s1/s1.txt', INPUT_DIR + 'test-data-s2/s2.txt', INPUT_DIR + 'test-data-s3/s3.txt'])
        ml.hac_horizontal(dataframe, OUT_DIR + 'hac-horizontal.png', OUT_DIR + 'hac-clusters-horizontal.txt')

        assert filecmp.cmp(OUT_DIR + 'hac-clusters-horizontal.txt', EXPECT_DIR + 'expected-hac-horizontal-clusters.txt', shallow=False)

    def test_hac_vertical(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-s1/s1.txt', INPUT_DIR + 'test-data-s2/s2.txt', INPUT_DIR + 'test-data-s3/s3.txt'])
        ml.hac_vertical(dataframe, OUT_DIR + 'hac-vertical.png', OUT_DIR + 'hac-clusters-vertical.txt')

        assert filecmp.cmp(OUT_DIR + 'hac-clusters-vertical.txt', EXPECT_DIR + 'expected-hac-vertical-clusters.txt', shallow=False)

    def test_ensemble_network(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-s1/s1.txt', INPUT_DIR + 'test-data-s2/s2.txt', INPUT_DIR + 'test-data-s3/s3.txt', INPUT_DIR + 'test-data-mixed-direction/mixed-direction.txt'])
        ml.ensemble_network(dataframe, OUT_DIR + 'ensemble-network.tsv')

        en = pd.read_table(OUT_DIR + 'ensemble-network.tsv')
        en = en.round(5)  # round values to 5 digits to account for numeric differences across machines
        expected = pd.read_table(EXPECT_DIR + 'expected-ensemble-network.tsv')
        expected = expected.round(5)

        assert en.equals(expected)

    def test_ensemble_network_single_line(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-single/single.txt'])
        ml.ensemble_network(dataframe, OUT_DIR + 'ensemble-network-single.tsv')

        en = pd.read_table(OUT_DIR + 'ensemble-network-single.tsv')
        en = en.round(5)
        expected = pd.read_table(EXPECT_DIR + 'expected-ensemble-network-single.tsv')
        expected = expected.round(5)

        assert en.equals(expected)

    def test_ensemble_network_empty(self):
        dataframe = ml.summarize_networks([INPUT_DIR + 'test-data-empty/empty.txt'])
        ml.ensemble_network(dataframe, OUT_DIR + 'ensemble-network-empty.tsv')

        en = pd.read_table(OUT_DIR + 'ensemble-network-empty.tsv')
        expected = pd.read_table(EXPECT_DIR + 'expected-ensemble-network-empty.tsv')

        assert en.equals(expected)
