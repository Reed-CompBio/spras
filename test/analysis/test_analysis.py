import pytest
from pathlib import Path
import src.analysis.summary.summary as summary

TEST_DIR = 'test/analysis/'


class TestAnalysis:
    """
    Test the summary statistics
    """
    def test_summary_ranked_ints(self):
        # Only include required arguments
        summary.run(TEST_DIR+'input/standardized-ranked.txt',TEST_DIR+'output/standardized-ranked-out.txt')

    def test_summary_ranked_floats(self):
        # Only include required arguments
        summary.run(TEST_DIR+'input/standardized-ranked-floats.txt',TEST_DIR+'output/standardized-ranked-floats-out.txt')

    def test_summary_unranked(self):
        # Only include required arguments
        summary.run(TEST_DIR+'input/standardized-unranked.txt',TEST_DIR+'output/standardized-unranked-out.txt')

    def test_summary_directed(self):
        # Only include required arguments
        summary.run(TEST_DIR+'input/standardized-ranked.txt',TEST_DIR+'output/standardized-ranked-directed-out.txt',directed=True)
