#!/usr/bin/python3

#
#  Copyright (C) 2018, 2019, 2020 Free Software Foundation, Inc.
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

## \copyright GNU Public License.
## \file sql.py Wrapper for the psycopg2 module

import epdb
import logging


class MapType(object):
    """A class to hold data for a map type"""

    def __init__(self):
        self.data = dict()
        self.data["name"] = None
        self.data["osm_id"] = None

    def get(self, item):
        return self.data[item]

    def put(self, item, value):
        self,data[item] = value

