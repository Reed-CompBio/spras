from filecmp import cmp
from pathlib import Path
from shutil import rmtree

from spras.attribution import attribute_algorithms
from spras.runner import algorithms

OUT_DIR = Path('test', 'attribution', 'output')
EXPECTED_DIR = Path('test', 'attribution', 'expected')

class TestAttribution:
    def test_attribute_algorithms(self):
        if OUT_DIR.exists():
            rmtree(str(OUT_DIR))

        # NOTE: This also serves as a dual test, confirming that the specified
        # DOIs in every `PRA#dois` are all valid
        attribution_files = [str(OUT_DIR / f"{name}.bib") for name in algorithms.keys()]
        attribution_all = str(OUT_DIR / "all.bib")

        attribute_algorithms(attribution_all, attribution_files)

        for file in attribution_files + [attribution_all]:
            assert cmp(file, EXPECTED_DIR / Path(file).name, shallow=False), \
                f"Algorithm attributions for {Path(file).stem} don't line up!"
