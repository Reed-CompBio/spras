import filecmp
import pandas as pd
import src.analysis.ml.ml as ml


TEST_DIR = 'test/analysis/input/test/'
OUT_DIR = 'test/analysis/output'
EXPECT_DIR = 'test/analysis/expected'

class TestML:

    def test_summarize_networks(self):
        dataframe = ml.summarize_networks([TEST_DIR+'s1.txt',TEST_DIR+'s2.txt',TEST_DIR+'s3.txt'])
        dataframe.to_csv(OUT_DIR+'/dataframe.csv')
        assert (filecmp.cmp(OUT_DIR+'/dataframe.csv', EXPECT_DIR+'/expected_df.csv'))

    def test_pca(self):
        dataframe = ml.summarize_networks([TEST_DIR+'s1.txt',TEST_DIR+'s2.txt',TEST_DIR+'s3.txt'])
        ml.pca(dataframe, OUT_DIR+'/pca.png', OUT_DIR+'/pca-components.txt', OUT_DIR+ '/pca-coordinates.txt')
        assert(filecmp.cmp(OUT_DIR+ '/pca-coordinates.txt', EXPECT_DIR+ '/expected_coords.txt'))
        assert(filecmp.cmp(OUT_DIR+'/pca-components.txt', EXPECT_DIR+'/expected_components.txt'))
    
    def test_hac(self):
        dataframe = ml.summarize_networks([TEST_DIR+'s1.txt',TEST_DIR+'s2.txt',TEST_DIR+'s3.txt'])
        ml.hac(dataframe,OUT_DIR+'/hac.png', OUT_DIR+'/hac-clusters.txt' )
        assert(filecmp.cmp(OUT_DIR+'/hac-clusters.txt', EXPECT_DIR+'/expected_clusters.txt'))

        