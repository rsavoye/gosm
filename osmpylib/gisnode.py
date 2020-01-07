
# 
# Copyright (C) 2017, 2018, 2019, 2020   Free Software Foundation, Inc.
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

import logging
#from shapely import wkb
from shapely import geometry
#import shapely

# http://toblerity.org/shapely/shapely.geometry.html
# '_ctypes_data', '_geom', '_get_coords', '_is_empty', '_lgeos', '_ndim', '_other_owned', '_repr_svg_', '_set_coords', 'almost_equals', 'area', 'array_interface_base', 'boundary', 'bounds', 'buffer', 'centroid', 'contains', 'convex_hull', 'coords', 'covers', 'crosses', 'ctypes', 'difference', 'disjoint', 'distance', 'empty', 'envelope', 'equals', 'equals_exact', 'geom_type', 'geometryType', 'has_z', 'impl', 'interpolate', 'intersection', 'intersects', 'is_closed', 'is_empty', 'is_ring', 'is_simple', 'is_valid', 'length', 'overlaps', 'project', 'relate', 'relate_pattern', 'representative_point', 'simplify', 'svg', 'symmetric_difference', 'to_wkb', 'to_wkt', 'touches', 'type', 'union', 'within', 'wkb', 'wkb_hex', 'wkt', 'xy']

class gisnode(geometry.base.BaseGeometry):
    """This class holds the data for a GIS waypoint object"""
    def __init__(self):
        self.data = dict()
        self.data['name'] = ""
        self.data['description'] = ""
        self.tags = dict()
        self.point = geometry.Point()

    def set(self, field, value=""):
        self.data[field] = value
        
    def get(self, field):
        return self.data[field]

    def settag(self, field, value=""):
        self.tags[field] = value
        
    def gettag(self, field):
        return self.tags[field]

