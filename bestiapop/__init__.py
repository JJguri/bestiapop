# -*- coding: utf-8 -*-
# Copyright (c) 2019-2020 Diego Perez (@darkquassar / https://linkedin.com/in/diegope) & Jonathan Ojeda (@JJguri / https://www.jojeda.com/)

from __future__ import print_function
__author__ = "Diego Perez <darkquasar7@gmail.com> & Jonathan Ojeda <jonathan.ojeda>"
__license__ = "???"
__stable__ = True
__version__ = "3.0"

import sys
sys.path.append("bestiapop")

import bestiapop
from .bestiapop import _main
from . import common
from . import connectors
from . import producers

#__version__ = get_versions()["version"]
#del get_versions