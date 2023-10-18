import spras.analysis.graphspace as graphspace
import spras.analysis.summary as summary

TEST_DIR = 'test/analysis/'

class TestAnalysis:
    """
    Test the summary statistics
    """
    # TODO: put back tests once summary.run is put back with mixed graphs
    # # test a ranked file of ints (1 - 10)
    # def test_summary_ranked_ints(self):
    #     summary.run(TEST_DIR + 'input/standardized-ranked.txt', TEST_DIR + 'output/standardized-ranked-out.txt')

    # # test a ranked file of floats (1.0 - 10.0)
    # def test_summary_ranked_floats(self):
    #     summary.run(TEST_DIR + 'input/standardized-ranked-floats.txt', TEST_DIR + 'output/standardized-ranked-floats-out.txt')

    # # test an unranked file (all ranks are 1)
    # def test_summary_unranked(self):
    #     summary.run(TEST_DIR + 'input/standardized-unranked.txt', TEST_DIR + 'output/standardized-unranked-out.txt')

    # # test a ranked file interpreted as a directed network (e.g. uses nx.DiGraph).
    # def test_summary_directed(self):
    #     summary.run(TEST_DIR + 'input/standardized-ranked.txt', TEST_DIR + 'output/standardized-ranked-directed-out.txt')

    # test GraphSpace json output on an undirected graph.
    def test_graphspace_ranked(self):
        graphspace.write_json(TEST_DIR + 'input/standardized-ranked.txt', TEST_DIR + 'output/standardized-ranked-undirected-gs.json', TEST_DIR + 'output/standardized-ranked-undirected-gs-style.json')

    # test GraphSpace json output on a directed graph.
    def test_graphspace_ranked_directed(self):
        graphspace.write_json(TEST_DIR + 'input/standardized-ranked.txt', TEST_DIR + 'output/standardized-ranked-directed-gs.json', TEST_DIR + 'output/standardized-ranked-directed-gs-style.json')
