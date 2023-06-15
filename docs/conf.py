"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from packaging.version import parse as parse_version
from typing_extensions import override

if sys.version_info >= (3, 11):
    from tomllib import load as toml_parse
else:
    from tomli import load as toml_parse


with open("../pyproject.toml", "rb") as f:
    pkg_meta: dict[str, str] = toml_parse(f)["tool"]["poetry"]

project = str(pkg_meta["name"])
copyright = f"{date.today().year}, ItsDrike"  # noqa: A001
author = "ItsDrike"

parsed_version = parse_version(pkg_meta["version"])
release = str(parsed_version)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    # Used to reference for third party projects:
    "sphinx.ext.intersphinx",
    # Used to include .md files:
    "m2r2",
    # Copyable codeblocks
    "sphinx_copybutton",
    # Towncrier changelog
    "sphinxcontrib.towncrier.ext",
]

autoclass_content = "both"
autodoc_member_order = "bysource"

autodoc_default_flags = {
    "members": "",
    "undoc-members": "code,error_template",
    "exclude-members": "__dict__,__weakref__",
}

# Automatically generate section labels:
autosectionlabel_prefix_document = True

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

add_module_names = False

autodoc_default_options = {
    "show-inheritance": True,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_favicon = "https://i.imgur.com/nPCcxts.png"

html_static_path = ["_static"]
html_css_files = ["extra.css"]

# -- Extension configuration -------------------------------------------------

# Third-party projects documentation references:
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}


# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# Enable multiple references to the same URL for m2r2
m2r_anonymous_references = True

# Changelog contains a lot of duplicate labels, since every subheading holds a category
# and these repeat a lot. Currently, m2r2 doesn't handle this properly, and so these
# labels end up duplicated. See: https://github.com/CrossNox/m2r2/issues/59
suppress_warnings = [
    "autosectionlabel.pages/changelog",
    "autosectionlabel.pages/code-of-conduct",
    "autosectionlabel.pages/contributing",
]

# Towncrier
towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = True
towncrier_draft_working_directory = Path(__file__).parents[1].resolve()


# -- Other options -----------------------------------------------------------


def mock_autodoc() -> None:
    """Mock autodoc to not add ``Bases: object`` to the classes, that do not have super classes.

    See also https://stackoverflow.com/a/75041544/20952782.
    """
    from sphinx.ext import autodoc

    class MockedClassDocumenter(autodoc.ClassDocumenter):
        @override
        def add_line(self, line: str, source: str, *lineno: int) -> None:
            if line == "   Bases: :py:class:`object`":
                return
            super().add_line(line, source, *lineno)

    autodoc.ClassDocumenter = MockedClassDocumenter


def override_towncrier_draft_format() -> None:
    """Monkeypatch sphinxcontrib.towncrier.ext to first convert the draft text from md to rst.

    We can use ``m2r2`` for this, as it's an already installed extension with goal
    of including markdown documents into rst documents, so we simply run it's converter
    somewhere within sphinxcontrib.towncrier.ext and include this conversion.

    Additionally, the current changelog format always starts the version with "Version {}",
    this doesn't look well with the version set to "Unreleased changes", so this function
    also removes this "Version " prefix.
    """
    import m2r2
    import sphinxcontrib.towncrier.ext
    from docutils import statemachine
    from sphinx.util.nodes import nodes

    orig_f = sphinxcontrib.towncrier.ext._nodes_from_document_markup_source

    def override_f(
        state: statemachine.State,
        markup_source: str,
    ) -> list[nodes.Node]:
        markup_source = markup_source.replace("## Version Unreleased changes", "## Unreleased changes")
        markup_source = markup_source.rstrip(" \n")

        # Alternative to 3.9+ str.removesuffix
        if markup_source.endswith("---"):
            markup_source = markup_source[:-3]

        markup_source = markup_source.rstrip(" \n")
        markup_source = m2r2.M2R()(markup_source)

        with open("foo.rst", "w") as f:
            f.write(markup_source)

        return orig_f(state, markup_source)

    sphinxcontrib.towncrier.ext._nodes_from_document_markup_source = override_f


mock_autodoc()
override_towncrier_draft_format()
