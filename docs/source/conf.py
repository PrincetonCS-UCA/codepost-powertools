"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import os
import sys

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

# Insert at front of path
sys.path[0:0] = [
    # Allow autodoc to find the src files
    os.path.abspath("../.."),
    # Add helpers folder
    os.path.abspath("./_helpers"),
]

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

try:
    import codepost_powertools.info as cptools_info

    project = cptools_info.package_name
    release = cptools_info.__version__
    github_url = cptools_info.github_url
except ImportError:
    project = "codepost-powertools"
    release = "0.0.0"
# only up to the major version
version = release[: release.rfind(".")]

author = "PrincetonCS-UCAs"
project_copyright = f"2023, {author}"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_toolbox.decorators",
]

root_doc = "index"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]

language = "en"  # English

pygments_style = "sphinx"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Configure the theme
html_theme = "sphinx_rtd_theme"
# https://sphinx-rtd-theme.readthedocs.io/en/latest/configuring.html
html_theme_options = {
    "style_external_links": True,
    "collapse_navigation": False,
    "sticky_navigation": False,
}

html_static_path = ["_static"]

# -- Extensions --------------------------------------------------------------

# Autodoc
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"
# To avoid evaluated type aliases (of which there are a lot), remove
# type hints from the signature
autodoc_typehints = "description"

# Intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "gspread": ("https://docs.gspread.org/en/latest/", None),
}

# Napoleon
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Others ------------------------------------------------------------------

# pylint: disable=wrong-import-position,import-error
# Automatically generate ``cptools`` cli help docs
import generate_cli_docs

generate_cli_docs.generate()
