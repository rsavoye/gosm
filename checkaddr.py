#!/usr/bin/python3

# 
# Copyright (C) 2018, 2019, 2020   Free Software Foundation, Inc.
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

# This class attempts to fix many common errors in OSM names, primarily
# because it break navigation. This script is a bit ugly and brute force,
# but does the trick for me. It's still hard to filter out all bad data,
# but this gets close.
import logging
import string
import epdb
import re
from sql import Postgis


class checkAddr(object):
    def __init__(self, dbname=None):
        self.post = Postgis()
        # Connect to database
        self.post.connect('localhost', dbname)
        self.addrs = self.post.query("SELECT osm_id,other_tags,wkb_geometry FROM points WHERE other_tags LIKE '%housenumber%';")
        print("Got %r addresses" % len(self.addrs))

    def getAddresses(self):
        return self.addrs

    def find_road(self, address):
        print("Looking for %r %r" % (address['addr:housenumber'], address['addr:street']))
        query = """SELECT road.name,ref,st_distance(St_ClosestPoint(road.wkb_geometry::geometry, addr.wkb_geometry::geometry), addr.wkb_geometry::geometry) as cp, St_AsText(addr.wkb_geometry) FROM points addr, lines road where addr.osm_id = '%s' ORDER BY cp asc LIMIT 5;""" % address['osm_id']
        roads = self.post.query(query)
        return roads
        for road in roads:
            print(road)

        
sql = checkAddr("Ouray")
addrs = sql.getAddresses()
for house in addrs:
    for road in sql.find_road(house):
        name = road['road.name']
        matched = False
        if name == house['addr:street'] or name == road['ref']:
            matched = True
            break
    if matched is True:
        print("\tMatched %s %s" % (house['addr:housenumber'], house['addr:street']))
    else:
        print("\tNo street for %s %s" % (house['addr:housenumber'], house['addr:street']))
