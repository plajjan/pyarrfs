#!/usr/bin/env python
#
# PyarrFS - a RAR reading file system
# Copyright (c) 2010, 2011 Kristian Larsson <kristian@spritelink.net>
#
# This file is licensed under the X11/MIT license, please see the file COPYING,
# distributed with PyarrFS for more details.
#


import sys

import pyarrfs.pyarrfs
try:
    pyarrfs.pyarrfs.main()
except KeyboardInterrupt:
    pass
sys.exit(0)
