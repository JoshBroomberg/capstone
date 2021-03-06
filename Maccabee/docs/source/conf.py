# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.
import os
import sys

# Path to the Maccabee package
sys.path.insert(0, os.path.abspath('../..'))

import sphinx_rtd_theme
import nbsphinx

# -- Project information -----------------------------------------------------

project = 'Maccabee'
copyright = '2020, Josh Broomberg'
author = 'Josh Broomberg'

# The full version, including alpha/beta/rc tags
release = '0.1.2'

master_doc = 'index'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax', # :math: support
    'sphinx.ext.napoleon', # google format docstrings
    'sphinx.ext.intersphinx', # links to external docs
    'sphinx.ext.viewcode', # source code links
    'sphinx.ext.autosectionlabel', # link to pages
    'sphinx_rtd_theme', # RTD them
    'nbsphinx' # rendering ipynbs
]

nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg', 'pdf'}",
    "--InlineBackend.rc={'figure.dpi': 96}",
]
# nbsphinx_input_prompt = '[%s]'
# nbsphinx_output_prompt = '[%s]'
nbsphinx_prompt_width = 0

add_module_names = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('http://pandas.pydata.org/pandas-docs/stable/', 'https://pandas.pydata.org/pandas-docs/stable/objects.inv'),
    'numpy': ('https://docs.scipy.org/doc/numpy/', 'https://docs.scipy.org/doc/numpy/objects.inv')
}

intersphinx_cache_limit = 3

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["**/.ipynb_checkpoints"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
