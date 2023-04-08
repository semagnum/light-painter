import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))

project = 'Light Painter'
copyright = '2023, Spencer Magnusson'
author = 'Spencer Magnusson'
html_logo = 'assets/logo.png'

html_context = {
    "display_github": True,
    "github_user": "semagnum",
    "github_repo": "light-painter",
    "github_version": "main",
    "conf_py_path": "/doc/",
}

extensions = ['myst_parser',
              'sphinx_favicon',
              ]

html_theme_options = {
    # Disable showing the sidebar. Defaults to 'false'
    'nosidebar': True,
}

source_suffix = ['.rst', '.md']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'doc']

autodoc_mock_imports = ['bl_ui', 'bpy', 'bmesh', 'mathutils']

html_theme = 'alabaster'
html_static_path = ['_static']

html_favicon = '_static/favicon.ico'
favicons = [
    {'static-file': 'favicon.ico'}
]