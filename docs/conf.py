# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Add the project root to the Python path ---------------------------------
# This is necessary to discover all the spras source code, otherwise auto-population of
# doc strings will be scoped to the `docs/` directory.
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SPRAS'
copyright = '2025, Anthony Gitter & Anna Ritz'
author = 'Anthony Gitter & Anna Ritz'
release = '0.2.0'

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
html_static_path = ['_static']
