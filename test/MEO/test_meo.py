import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.meo import MEO, write_properties

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/MEO/'
OUT_FILE = TEST_DIR + 'output/edges.txt'


class TestMaximumEdgeOrientation:
    """
    Run Maximum Edge Orientation in the Docker image
    """
    def test_meo_required(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        MEO.run(edges=TEST_DIR + 'input/meo-edges.txt',
                sources=TEST_DIR + 'input/meo-sources.txt',
                targets=TEST_DIR + 'input/meo-targets.txt',
                output_file=OUT_FILE)
        assert out_path.exists()

    def test_meo_all_optional(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Include all optional arguments
        MEO.run(edges=TEST_DIR + 'input/meo-edges.txt',
                sources=TEST_DIR + 'input/meo-sources.txt',
                targets=TEST_DIR + 'input/meo-targets.txt',
                output_file=OUT_FILE,
                max_path_length=3,
                local_search='No',
                rand_restarts=10)
        assert out_path.exists()

    def test_meo_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No edges
            MEO.run(sources=TEST_DIR + 'input/meo-sources.txt',
                    targets=TEST_DIR + 'input/meo-targets.txt',
                    output_file=OUT_FILE)

        with pytest.raises(ValueError):
            # No path_output
            write_properties(filename=Path('.'),
                             edges=TEST_DIR + 'input/meo-edges.txt',
                             sources=TEST_DIR + 'input/meo-sources.txt',
                             targets=TEST_DIR + 'input/meo-targets.txt',
                             edge_output=OUT_FILE)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_meo_singularity(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        MEO.run(edges=TEST_DIR + 'input/meo-edges.txt',
                sources=TEST_DIR + 'input/meo-sources.txt',
                targets=TEST_DIR + 'input/meo-targets.txt',
                output_file=OUT_FILE,
                container_framework="singularity")
        assert out_path.exists()
