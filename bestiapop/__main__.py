from __future__ import absolute_import

import os
import sys

# If we are running with `python -m bestiapop`
# Add the current dir to the PATH env so as to make BestiaPop available as a package
if __package__ == '':
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

# This is convoluted but essentially, by importing the bestiapop cli (bestiapop.py) this way
# we can ensure that bestiapop will run whether we use `python -m bestiapop` or `python bestiapop`
# (the latter whilst being in the repository root directory since it considers the "bestiapop" folder as a package)
import bestiapop.bestiapop as bestiapop

if __name__ == '__main__':
    bestiapop.main()