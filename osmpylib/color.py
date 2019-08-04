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

        # Access
        self.default['private'] = {"color": "gray", "id": "GrayLine", "width": 3.0}

        # highway=path
        self.default['hiking'] = {"color": "brown", "id": "BrownLine", "width": 3.0}
        self.default['mountain_hiking'] = {"color": "orange", "id": "OrangeLine", "width": 3.0}
        self.default['demanding_mountain_hiking'] = {"color": "purple", "id": "PurpleLine", "width": 3.0}
        self.default['alpine_hiking'] = {"color": "skyblue", "id": "SkyBlueLine", "width": 3.0}
        self.default['demanding_alpine_hiking'] = {"color": "skyblue", "id": "SkyBlueLine", "width": 3.0}
        self.default['difficult_alpine_hiking'] = {"color": "skyblue", "id": "SkyBlueLine", "width": 3.0}

        self.default['0'] = {"color": "brown", "id": "BrownLine", "width": 3.0}
        self.default['1'] = {"color": "green", "id": "GreenLine", "width": 3.0}
        self.default['2'] = {"color": "blue", "id": "BlueLine", "width": 3.0}
        self.default['3'] = {"color": "red", "id": "RedLine", "width": 3.0}
        self.default['4'] = {"color": "black", "id": "BlackLine", "width": 3.0}

        # Tracktype
        self.default['grade1'] = {"color": "brown", "id": "BrownLine", "width": 2.0}
        self.default['grade2'] = {"color": "green", "id": "BrownLine", "width": 2.0}
        self.default['grade3'] = {"color": "blue", "id": "BrownLine", "width": 2.0}
        self.default['grade4'] = {"color": "red", "id": "BrownLine", "width": 2.0}

        # highway=*
        self.default['trunk'] = { "color": "orange", "id": "Wide Red/Orange", "width": 3.0}
        self.default['motorway'] = { "color": "lightpink3", "id": "WideLightPink", "width": 3.0}
        self.default['primary'] = { "color": "burlywood1", "id": "WideLightOrange", "width": 3.0}
        self.default['tertiary'] = { "color": "white", "id": "WideWhite", "width": 3.0}
        self.default['secondary'] = { "color": "yellow", "id": "WideYellow", "width": 3.0}
        # Space cadets... fix later when possible
        self.default['road'] = { "color": "black", "id": "gray", "width": 3.0}
        self.default['service'] = { "color": "red", "id": "RedLine", "width": 3.0}
        self.default['motorway_link'] = { "color": "red", "id": "RedLine", "width": 3.0}
        self.default['secondary_link'] = { "color": "yellow", "id": "YellowLine", "width": 3.0}
        self.default['trunk_link'] = { "color": "salmon1", "id": "OrangeLine", "width": 3.0}
        self.default['living_street'] = { "color": "white", "id": "whiteLine", "width": 3.0}

        # Probably added by me
        self.default['unclassified'] = { "color": "white", "id": "whiteLine", "width": 3.0}
        self.default['residential']  = { "color": "white", "id": "whiteLine", "width": 3.0}
        self.default['track'] = { "color": "brown", "id": "DottedBrown", "width": 3.0}
        self.default['4wd_only'] = { "color": "black", "id": "dotted brown", "width": 3.0}

        # handled by self.trails
        #self.default['path']= { "color": "black", "id": "dotted red", "width": 3.0}
        self.default['driveway'] = { "color": "white", "id": "whiteLine", "width": 3.0}
        # a footway is a sidewalk, so we don't care
        #self.default['footway'] = { "color": "black", "id": "dotted red", "width": 3.0}
        self.default['cycleway'] = { "color": "black", "id": "dotted red", "width": 3.0}
        self.default['bridleway'] = { "color": "black", "id": "dotted red", "width": 3.0}

        # Ignore surface tag for now
        #self.default['dirt'] = { "color": "black", "id": "dotted red", "width": 3.0}

        # Ignore tracktype tag for now
        #self.default['grade1'] = { "color": "black", "id": "dotted red", "width": 3.0}
        
        # For smoothness tag
        self.default['impassable'] = { "color": "blue", "id": "blue", "width": 3.0}
        self.default['poor'] = { "color": "blue", "id": "blue", "width": 3.0}
        self.default['bad'] = { "color": "blue", "id": "blue", "width": 3.0}
        self.default['horrible'] = { "color": "blue", "id": "blue", "width": 3.0}
        self.default['very_horrible'] = { "color": "blue", "id": "blue", "width": 3.0}

        # 
        self.default['motor_vehicle'] = { "color": "blue", "id": "blue", "width": 1.0}
        self.default['horse'] = { "color": "blue", "id": "blue", "width": 1.0}
        self.default['atv'] = { "color": "blue", "id": "blue", "width": 1.0}
        self.default['bicycle'] = { "color": "blue", "id": "blue", "width": 1.0}
        
        self.linestyles = list()
        for key,val in self.default.items():
            lstyle = styles.LineStyle(id=val['id'], color=val['color'], width=val['width'])
            self.linestyles.append(styles.Style(styles=[lstyle]))
            self.styles = list()

        self.description = ""

    def make_hex(self, index, alpha=0xff):
        try:
            color = self.default[index]['color']
        except:
            color = 'green'
            logging.warning("Index %s doesn't exist!" % index)
        base = Color(color).hex_l
        base = base.replace('#', 'ff')
        # aa = alpha
        # rr = rgb[0]
        # gg = rgb[1]
        # bb = rgb[2]
        # return "#{aa}{rr}{gg}{bb}"
        return base
        
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

        index = data['highway']
        #logging.debug("Looking for road type: %r" % index)
        width = 3.0
        try:
            id = self.default[index]['id']
            width = self.default[index]['width']
            color = self.make_hex(index)
        except:
            color = 'pink'

        self.description = ""

        # Tags that go in the description popyup
        if 'service' in data:
            if data['service'] == 'driveway':
                color =  self.make_hex('driveway')
                self.description += "Private Driveway"
        else:
            if 'name' in data:
                self.description += "<br>Name: " + data['name']
        if 'alt_name' in data:
            self.description += "<br>Alt Name: " + data['alt_name']
        if 'tracktype' in data:
            if data['tracktype'] == 'yes':
                color =  self.make_hex('tracktype')
                self.description += "<br>Tracktype: " + data['tracktype']
        if 'motor_vehicle' in data:
            if data['motor_vehicle'] == 'yes':
                color =  self.make_hex('motor_vehicle')
                self.description += "<br>Vehicles OK: yes"
        if 'access' in data:
            if data['access'] == 'private':
                color =  self.make_hex('private')
        if 'atv' in data:
            if data['atv'] == 'yes':
                color =  self.make_hex('atv')
                self.description += "<br>ATVs OK: yes"
        if 'horse' in data:
            if data['horse'] == 'yes':
                color =  self.make_hex('horse')
                self.description += "<br>Horse OK: yes"
        if 'bicycle' in data:
            if data['bicycle'] == 'yes':
                color =  self.make_hex('bicycle')
                self.description += "<br>Bicycle OK: yes"
        if '4wd_only' in data:
            if data['4wd_only'] == 'yes':
                color =  self.make_hex('4wd_only')
            self.description += "<br>4wd Only: " + data['4wd_only']
        if 'smoothness' in data:
            pass
        if 'surface' in data:
            pass
        self.description += "<p>Data: %r" % data

        lstyle = styles.LineStyle(color=color, width=width)
        self.styles = styles.Style(styles=[lstyle])

        #print(self.description)
        return self.styles, self.description

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
            #epdb.st()
            color = self.make_hex(index)
            id = self.default[index]['id']
            width = self.default[index]['width']
            #self.description += "<br>Sac_scale: " + data['sac_scale']
        if 'mtb:scale:imba' in data:
            self.description += "<br>Mnt Scale: " + str(data['mtb:scale:imba'])
        if 'mtb:scale' in data:
            pass
            # self.description += "<br>Mnt Scale: " + str(data['mtb:scale'])

        # Create the description pop-up
        if 'surface' in data:
            self.description += "<br>Surface: " + data['surface']
        if 'bicycle' in data:
            self.description += "<br>Bicycle: " + data['bicycle']
        if 'horse' in data:
            self.description += "<br>Horse: " + data['horse']
        if 'atv' in data:
            self.description += "<br>Atv: " + data['atv']
        if 'access' in data:
            self.description += "<br>Access: " + data['access']
        if 'tracktype' in data:
            self.description += "<br>Tracetype: " + data['tracktype']
        if 'trail_visibility' in data:
            self.description += "<br>Visability: " + data['trail_visibility']
        if 'motor_vehicle' in data:
            self.description += "<br>Motor Vehicle: " + data['motor_vehicle']

        lstyle = styles.LineStyle(color=color, width=width)
        self.styles = styles.Style(styles=[lstyle])

        #print(self.description)
        return self.styles, self.description

    def addresses(self, data):
        #print(data)
        self.description = ""
        color = "ffffff00"
        id = data['osm_id']
        if 'addr_street' in data:
            self.description = "%s %s" % (str(data['addr_housenumber']), data['addr_street'])
        # label = styles.LabelStyle(color='black', scale=1.0)
        icon = styles.IconStyle(icon_href="icons/mm_building.png")
        self.styles = styles.Style(styles=[icon])

        return self.styles, self.description
    
    def milestones(self, data):
        #print(data)
        self.description = ""
        id = data['osm_id']
        num = data['name']
        street= data['alt_name']
        self.description = "%s Highway %s" % (num, street)

        icon = styles.IconStyle(icon_href="icons/mm_highway_milestone.png")
        self.styles = styles.Style(styles=[icon])

        return self.styles, self.description

    def landingzones(self, data):
        #print(data)
        self.description = ""

        icon = styles.IconStyle(icon_href="icons/heliport.png")
        self.styles = styles.Style(styles=[icon])

        return self.styles, self.description

    def firewater(self, data):
        self.description = ""

        if 'water_tank' in data:
            icon = styles.IconStyle(icon_href="icons/mx_fire_hydrant_type_pillar.png")

        if 'emergency' in data:
            if data['emergency'] == "fire_hydrant":
                icon = styles.IconStyle(icon_href="icons/mx_fire_hydrant_type_pillar.png")
            elif data['emergency'] == "water_tank":
                icon = styles.IconStyle(icon_href="icons/cistern.png")
        self.styles = styles.Style(styles=[icon])

        return self.styles, self.description

if __name__ == '__main__':
    ms = MapStyle("ns='{http://www.opengis.net/kml/2.2}'")
    indata = {"name": "Fgake hiking", "sac_scale": "hiking", "mtb:scale": "3"}
    outdata = ms.trails(indata)
    # print(outdata[1])

    indata = {"name": "Fake demanding mountain hiking", "sac_scale": "demanding_mountain_hiking", "mtb:scale": "3", "atv": "yes"}
    outdata = ms.trails(indata)
    # print(outdata[1])
          
    indata = {"name": "Fake difficult Alpine hiking", "sac_scale": "difficult_alpine_hiking", "mtb:scale": "4", "motor_vehicle": "no"}
    outdata = ms.trails(indata)
    # print(outdata[1])

