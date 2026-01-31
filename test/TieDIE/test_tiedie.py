import shutil
from pathlib import Path

import pytest

from spras.config.container_schema import ContainerFramework, ProcessedContainerSettings
from spras.tiedie import TieDIE, TieDIEParams

TEST_DIR = Path('test', 'TieDIE')
OUT_FILES = TEST_DIR / 'output' / 'output1' / 'tiedie_pathway.txt'
OUT_FILES_1 = TEST_DIR / 'output' / 'output2' / 'tiedie_pathway_alternative.txt'

class TestTieDIE:
    """
    Run the TieDIE algorithm on the example input files
    """

    def test_tiedie_required(self):
        out_path = Path(OUT_FILES)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        TieDIE.run({"sources": TEST_DIR / 'input' / 'source1.txt',
                    "targets": TEST_DIR / 'input' / 'target1.txt',
                    "edges": TEST_DIR / 'input' / 'pathway1.txt'},
                    output_file=OUT_FILES)
        assert out_path.exists()

    def test_tiedie_alternative_graph(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        TieDIE.run({"sources": TEST_DIR / 'input' / 'source2.txt',
                    "targets": TEST_DIR / 'input' / 'target2.txt',
                    "edges": TEST_DIR / 'input' / 'pathway2.txt'},
                    output_file=OUT_FILES_1)
        assert out_path.exists()

    def test_tiedie_some_optional(self):
        out_path = Path(OUT_FILES)
        out_path.unlink(missing_ok=True)
        # Include optional argument
        TieDIE.run({"sources": TEST_DIR / 'input' / 'source1.txt',
                    "targets": TEST_DIR / 'input' / 'target1.txt',
                    "edges": TEST_DIR / 'input' / 'pathway1.txt'},
                    output_file=OUT_FILES,
                    args=TieDIEParams(
                        s=1.1,
                        p=2000,
                        pagerank=True))
        assert out_path.exists()

    def test_tiedie_all_optional(self):
        out_path = Path(OUT_FILES)
        out_path.unlink(missing_ok=True)
        # Include optional argument
        TieDIE.run({"sources": TEST_DIR / 'input' / 'source1.txt',
                    "targets": TEST_DIR / 'input' / 'target1.txt',
                    "edges": TEST_DIR / 'input' / 'pathway1.txt'},
                    output_file=OUT_FILES,
                    args=TieDIEParams(s=1.1,
                        c=4,
                        p=2000,
                        pagerank=True,
                        all_paths=True))
        assert out_path.exists()

    def test_tiedie_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No edges file
            TieDIE.run({"sources": TEST_DIR / 'input' / '/source1.txt',
                        "targets": TEST_DIR / 'input' / '/target1.txt'},
                        output_file=OUT_FILES)

    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_tiedie_singularity(self):
        out_path = Path(OUT_FILES)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        TieDIE.run({"sources": TEST_DIR / 'input' / 'source1.txt',
                    "targets": TEST_DIR / 'input' / 'target1.txt',
                    "edges": TEST_DIR / 'input' / 'pathway1.txt'},
                    output_file=OUT_FILES,
                    args=TieDIEParams(
                        s=1.1,
                        p=2000,
                        pagerank=True),
                    container_settings=ProcessedContainerSettings(framework=ContainerFramework.singularity))
        assert out_path.exists()
