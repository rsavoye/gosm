# 
#   Copyright (C) 2017, 2018, 2019   Free Software Foundation, Inc.
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
import re
import epdb
from fastkml import styles
from colour import Color

# https://wiki.openstreetmap.org/wiki/Hiking_Maps
# https://wiki.openstreetmap.org/wiki/Key:highway
# https://www.webucator.com/blog/2015/03/python-color-constants-module


class MapStyle(object):
    """
   """
    def __init__(self, ns):
        self.ns = ns
        self.description = ""
        self.default = dict()
        self.default['hiking'] = {"color": "brown", "id": "BrownLine", "width": 3.0}
        self.default['mountain_hiking'] = {"color": "ff00a5ff", "id": "OrangeLine", "width": 3.0}
        self.default['demanding_mountain_hiking'] = {"color": "ff800080", "id": "PurpleLine", "width": 3.0}
        self.default['alpine_hiking'] = {"color": "ff000080", "id": "SkyBlueLine", "width": 3.0}
        self.default['demanding_alpine_hiking'] = {"color": "ff000080", "id": "SkyBlueLine", "width": 3.0}
        self.default['difficult_alpine_hiking'] = {"color": "ff000080", "id": "SkyBlueLine", "width": 3.0}

        self.default['0'] = {"color": "brown", "id": "BrownLine", "width": 3.0}
        self.default['1'] = {"color": "green", "id": "GreenLine", "width": 3.0}
        self.default['2'] = {"color": "blue", "id": "BlueLine", "width": 3.0}
        self.default['3'] = {"color": "red", "id": "RedLine", "width": 3.0}
        self.default['4'] = {"color": "black", "id": "BlackLine", "width": 3.0}

        self.linestyles = list()
        for key,val in self.default.items():
            lstyle = styles.LineStyle(id=val['id'], color=val['color'], width=val['width'])
            self.linestyles.append(styles.Style(styles=[lstyle]))
            self.styles = list()

    def getStyles(self):
        return self.linestyles

    def roads(self, data):
        """
        trunk - Wide Red/Orange, "salmon1"
        motorway - Wide pink,  "lightpink3"
        primary - Wide light orange, "burlywood1"
        tertiary - Wide white, "white"
        secondary - Wide Yellow, "yellow"
        unclassified - white, "white"
        residential - white, "white"
        track - dotted brown, "brick"
        path - dotted red, "red"
        service - white, "white"
        footway - dotted red, "red"
        road - gray, "gray"
        """
        pass
    def trails(self, data):
        #print(data)
        self.description = ""
        color = "ffffff00"
        if 'name' in data:
            name = data['name']
        id = data['osm_id']
        width = 3
        if 'sac_scale' in data:
            index = data['sac_scale']
            color = self.default[index]['color']
            #color = Color(color).hex_l.replace('#', 'ff')
            id = self.default[index]['id']
            width = self.default[index]['width']
            #self.description += "\nSac_scale: " + data['sac_scale']
        if 'mtb:scale:imba' in data:
            self.description += "\nMnt Scale: " + str(data['mtb:scale:imba'])
        if 'mtb:scale' in data:
            pass
            # self.description += "\nMnt Scale: " + str(data['mtb:scale'])

        # Create the description pop-up
        if 'surface' in data:
            self.description += "\nSurface: " + data['surface']
        if 'bicycle' in data:
            self.description += "\nBicycle: " + data['bicycle']
        if 'horse' in data:
            self.description += "\nHorse: " + data['horse']
        if 'atv' in data:
            self.description += "\nAtv: " + data['atv']
        if 'access' in data:
            self.description += "\nAccess: " + data['access']
        if 'tracktype' in data:
            self.description += "\nTracetype: " + data['tracktype']
        if 'trail_visibility' in data:
            self.description += "\nVisability: " + data['trail_visibility']
        if 'motor_vehicle' in data:
            self.description += "\nMotor Vehicle: " + data['motor_vehicle']

        lstyle = styles.LineStyle(color=color, width=width)
        self.styles = styles.Style(styles=[lstyle])

        print(self.description)
        return self.styles, self.description


if __name__ == '__main__':
    ms = MapStyle("ns='{http://www.opengis.net/kml/2.2}'")
    indata = {"name": "Fake hiking", "sac_scale": "hiking", "mtb:scale": "3"}
    outdata = ms.trails(indata)
    print(outdata[1])

    indata = {"name": "Fake demanding mountain hiking", "sac_scale": "demanding_mountain_hiking", "mtb:scale": "3", "atv": "yes"}
    outdata = ms.trails(indata)
    print(outdata[1])
          
    indata = {"name": "Fake difficult Alpine hiking", "sac_scale": "difficult_alpine_hiking", "mtb:scale": "4", "motor_vehicle": "no"}
    outdata = ms.trails(indata)
    print(outdata[1])

