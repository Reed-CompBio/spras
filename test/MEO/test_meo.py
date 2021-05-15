import pytest
from pathlib import Path
from src.meo import MEO, write_properties

TEST_DIR = 'test/MEO/'

# Must run from the root of the spras repository
MEO.run(edges='test/MEO/input/meo-edges.txt',
        sources='test/MEO/input/meo-sources.txt',
        targets='test/MEO/input/meo-targets.txt',
        output_file='test/MEO/output/edges.txt')
