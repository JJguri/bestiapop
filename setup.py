import sys
from distutils.core import setup
from os import path

# Newer packaging standards may recommend removing the current dir from the
# path, add it back if needed.
if '' not in sys.path:
    sys.path.insert(0, '')

# *** Distutils setup and metadata ***

# Development Status "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
_CLASSIFIERS = \
"""
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
Intended Audience :: Information Technology
Intended Audience :: Science/Research
License :: OSI Approved :: BSD License
Programming Language :: Cython
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Topic :: Scientific/Engineering
Topic :: Database
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Unix
Operating System :: POSIX :: Linux
Operating System :: MacOS :: MacOS X
Operating System :: Microsoft :: Windows
"""

# *** DESCRIPTION ***

# read the contents of README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
    
short_description = "Climate Data Mining Automation Framework"
long_description = long_description,
long_description_content_type = 'text/markdown'

_PACKAGES = [
    'bestiapop',
    'bestiapop.common',
    'bestiapop.connectors',
    'bestiapop.producers'
]

_VERSION = '3.0.8'

_KEYWORDS = [
    'silo',
    'apsim',
    'nasapower',
    'dssat',
    'met',
    'wth',
    'crop model',
    'crop modelling',
    'crops',
    'agriculture',
    'data science',
    'climate',
    'weather',
    'automation'
]

_INSTALLREQUIRES = [
    'coloredlogs>=10.0',
    'h5netcdf>=0.7.4',
    'jinja2>=2.11.1',
    'numpy>=1.16.2',
    'pandas>=0.24.2',
    'requests>=2.21.0',
    's3fs>=0.4.0',
    'tabulate>=0.8.3',
    'tqdm>=4.39.0',
    'xarray>=0.14.0'
]

setup(
  name = 'bestiapop',
  packages = _PACKAGES,
  classifiers = [x for x in _CLASSIFIERS.split("\n") if x],
  version = _VERSION,
  license = 'bsd-3-clause',
  description = short_description,
  long_description = long_description,
  author = 'Diego Perez & Jonathan Ojeda',
  author_email = 'darkquasar7@gmail.com',
  url = 'https://bestiapop.readthedocs.io/en/latest/',
  download_url = 'https://github.com/JJguri/bestiapop/archive/v{}.tar.gz'.format(_VERSION),
  keywords = _KEYWORDS,
  install_requires = _INSTALLREQUIRES,
  python_requires = '>=3.6'
)