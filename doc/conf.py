import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))

project = 'Light Paint'
copyright = '2023, Spencer Magnusson'
author = 'Spencer Magnusson'
html_logo = 'assets/logo.png'

html_context = {
    "display_github": True,
    "github_user": "semagnum",
    "github_repo": "lightpaint",
    "github_version": "main",
    "conf_py_path": "/doc/",
}

extensions = ['sphinx.ext.autodoc',
              'sphinx_autodoc_typehints',
              'myst_parser',
              'sphinx_favicon',
              ]

source_suffix = ['.rst', '.md']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'doc']

autodoc_mock_imports = ['bl_ui', 'bpy', 'bmesh', 'mathutils']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_favicon = '_static/favicon.ico'
favicons = [
    {'static-file': 'favicon.ico'}
]