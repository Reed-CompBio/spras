# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Add the project root to the Python path ---------------------------------
# This is necessary to discover all the spras source code, otherwise auto-population of
# doc strings will be scoped to the `docs/` directory.
import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SPRAS'
copyright = '2025, Anthony Gitter & Anna Ritz'
author = 'Anthony Gitter & Anna Ritz'

# Attempt to get the version from package metadata
try:
    version = get_version("spras")  # This will pull the version from pyproject.toml
except PackageNotFoundError:
    version = "unknown"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# The sphinx autodoctor extension will automatically generate documentation for all
# classes and functions in the spras package that have docstrings and that have been
# configured via the spras.rst file.
extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_context = {
    "display_github": True,
    "github_user": "Reed-CompBio",
    "github_repo": "spras",
    "github_version": "main/docs/",
}
html_static_path = ['_static']
