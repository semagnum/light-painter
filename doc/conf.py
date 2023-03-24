import os
import sys

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))

project = 'Light Paint'
copyright = '2023, Spencer Magnusson'
author = 'Spencer Magnusson'

extensions = ['sphinx.ext.autodoc',
              'sphinx_autodoc_typehints',
              # 'sphinx-favicon',
              ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'doc']

autodoc_mock_imports = ['bl_ui', 'bpy', 'bmesh', 'mathutils']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# html_favicon = '_static/favicon.ico'
# favicons = [
#     {'static-file': 'favicon.ico'}
# ]