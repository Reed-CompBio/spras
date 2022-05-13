from pathlib import Path

TEST_DIR = 'test/LocalNeighborhood/'
OUT_FILE = TEST_DIR + 'output/edges.txt'

class TestLocalNeighborhood:
    """

    """
    def test_ln(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)

        assert out_path.exists()
