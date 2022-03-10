import pytest
from pathlib import Path
from src.meo import MEO, write_properties

TEST_DIR = 'test/MEO/'


class TestMaximumEdgeOrientation:
    """
    Run Maximum Edge Orientation in the Docker image
    """
    def test_meo_required(self):
        # Only include required arguments
        MEO.run(edges=TEST_DIR + 'input/meo-edges.txt',
                sources=TEST_DIR + 'input/meo-sources.txt',
                targets=TEST_DIR + 'input/meo-targets.txt',
                output_file=TEST_DIR + 'output/edges.txt')

    def test_meo_all_optional(self):
        # Include all optional arguments
        MEO.run(edges=TEST_DIR + 'input/meo-edges.txt',
                sources=TEST_DIR + 'input/meo-sources.txt',
                targets=TEST_DIR + 'input/meo-targets.txt',
                output_file=TEST_DIR + 'output/edges.txt',
                max_path_length=3,
                local_search='No',
                rand_restarts=10)

    def test_meo_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No edges
            MEO.run(sources=TEST_DIR + 'input/meo-sources.txt',
                    targets=TEST_DIR + 'input/meo-targets.txt',
                    output_file=TEST_DIR + 'output/edges.txt')

        with pytest.raises(ValueError):
            # No path_output
            write_properties(filename=Path('.'),
                             edges=TEST_DIR + 'input/meo-edges.txt',
                             sources=TEST_DIR + 'input/meo-sources.txt',
                             targets=TEST_DIR + 'input/meo-targets.txt',
                             edge_output=TEST_DIR + 'output/edges.txt')
