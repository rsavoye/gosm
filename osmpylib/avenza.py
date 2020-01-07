#!/usr/bin/python3

# 
# Copyright (C) 2019, 2020   Free Software Foundation, Inc.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 

## \file avenza.py manipulate Avenza maps (GeoPDF)

import os
import sys
import logging
import epdb
from subprocess import PIPE, Popen, STDOUT
from vrt import gdalVRT


class Avenza(object):
    def __init__(self, options=None):
        """Class to hold data"""
        self.options = options
        self.layer = None

    def applyLayer(self, layer=None):
        if layer is None and self.layer is None:
            return 0
        self.layer = layer   
        vrt = gdalVRT(self.options)
        vrt.create(layer)
        vrt.apply()

    def dump(self):
        self.options.dump()
