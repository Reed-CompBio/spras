import glob
from importlib.metadata import version
from os.path import basename, dirname, isfile, join

modules = glob.glob(join(dirname(__file__), "*.py"))

__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

# Import version info from package metadata, which is populated from pyproject.toml
# Note that this version will only be populated correctly in source code if the `spras` module
# is installed (as opposed to operating solely from a conda env).
__version__ = version("spras")
