from __future__ import absolute_import

import os
import sys

# If we are running with `python -m bestiapop`
# Add the current dir to the PATH env so as to make BestiaPop available as a package
if __package__ == '':
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

from bestiapop import _main

if __name__ == '__main__':
    sys.exit(_main.main())