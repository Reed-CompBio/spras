import filecmp
import pandas as pd
import src.analysis.ml.ml as ml


TEST_DIR = 'test/ml/test/'
OUT_DIR = 'test/ml/output/'
EXPECT_DIR = 'test/ml/expected/'

class TestML:

    def test_summarize_networks(self):
        dataframe = ml.summarize_networks([TEST_DIR+'s1.txt',TEST_DIR+'s2.txt',TEST_DIR+'s3.txt',TEST_DIR+'longName.txt', TEST_DIR+'longName2.txt', TEST_DIR+'empty.txt'])
        dataframe.to_csv(OUT_DIR+'dataframe.csv')
        dataframe.to_csv(EXPECT_DIR+'expected_df.csv')

        assert (filecmp.cmp(OUT_DIR+'dataframe.csv', EXPECT_DIR+'expected_df.csv'))

    def test_pca(self):
        dataframe = ml.summarize_networks([TEST_DIR+'s1.txt',TEST_DIR+'s2.txt',TEST_DIR+'s3.txt'])
        ml.pca(dataframe, OUT_DIR+'pca/pca.png', OUT_DIR+'pca/pca-components.txt', OUT_DIR+ 'pca/pca-coordinates.txt')
        comp = pd.read_csv(OUT_DIR+'pca/pca-coordinates.txt').round(5)
        excepted = pd.read_csv(EXPECT_DIR+ 'expected_coords.txt').round(5)
        assert(comp.equals(excepted))
    
    def test_hac(self):
        dataframe = ml.summarize_networks([TEST_DIR+'s1.txt',TEST_DIR+'s2.txt',TEST_DIR+'s3.txt'])
        ml.hac(dataframe,OUT_DIR+'hac/hac.png', OUT_DIR+'hac/hac-clusters.txt' )
        assert(filecmp.cmp(OUT_DIR+'hac/hac-clusters.txt', EXPECT_DIR+'expected_clusters.txt'))

    