#!/usr/bin/python3

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

import googlemaps
import pprint
import re
import sys
from datetime import tzinfo, timedelta, datetime
import html2text
from sys import argv

if argv[1] is None:
    destination = "1303 Upper Moon Gulch, Rollinsville, CO"
else:
    destinations = list()
    destinations.append(argv[1] + ", Black Hawk, CO")

stations = ["5927 Magnolia Road, Nederland, CO" ,"3999 Highway 72, Pinecliffe, CO", "135 Tolland Road, Rollinsville, CO", "448 Pine Dr., Black Hawk, CO","14908 Highway 119, Black Hawk, CO", "146 North Dory Lakes Drive, Black Hawk, CO", "660 Highway 46, Black Hawk, CO", "2236 Smith Hill Road, Golden, CO", "4611 Smith Hill Road, Golden, CO", "495 Apex Road, Black Hawk, CO"]

names = ["Station 1", "Station 2", "Station 3", "Station 4", "Station 5", "Station 6", "Station 7 ", "Station 8 ", "Station 9 ", "Station 10"]

coordinates = ["39.9768221,-105.417122", "39.9392044,-105.4404452", "39.91756700000001,-105.505307", "39.89200400000001,-105.4813322", "39.864616,-105.4656415","39.8475062,-105.476561", "39.8400306,-105.4811873", "39.7445193,-105.229805", "39.82077049999999,-105.4081804", "39.8234031,-105.5235759"]

apikey="AIzaSyCuTm3ux305teZ2cz9AS-zAZlY0sZ1-U1w"

gmaps = googlemaps.Client(apikey)

infile = open("/work/Mapping/MapData/TLFPD/x")
#destinations = infile.readlines()
for destination in destinations:
    destination = destination.replace('\n', '')
    now = datetime.now()
    dest = gmaps.distance_matrix(stations, destination, mode="driving", units="imperial", departure_time=now)

    data = dict()
    addrs = dict()
    i = 0
    for row in dest['rows']:
        try:
            index = row['elements'][0]['distance']['text'].replace(' mi', '')
        except KeyError:
            continue
        data[index] = names[i]
        addrs[index] = stations[i]
        i += 1

    best = 100.0
    for k,v in data.items():
        distance = float(k.replace(',', '.'))
        #print("%r %r" % (best, distance))
        if  distance < best:
            best = distance

    try:
        closest = data[str(best)]
    except KeyError:
        print("Address %r not found" % destination)
        continue

    print("Closest station is: %r, %r miles away" % (closest, best))

    origin = addrs[str(best)]

    # Look up an address with reverse geocoding
    #geocode_result = gmaps.geocode('Boulder, CO')
    #lat = geocode_result[0]["geometry"]['location']['lat']
    #lng = geocode_result[0]["geometry"]['location']['lng']

    #reverse_geocode_result = gmaps.reverse_geocode((lat, lng))

    here = gmaps.geolocate()
    whereami = gmaps.reverse_geocode(here['location'])

    directions_result = gmaps.directions(origin,
                                        destination,
                                         mode="driving",
                                         language=None,
                                         avoid=None,
                                         units="imperial",
                                         departure_time=now)


    print("Directions to: %r from %r" % (destination.replace(', Black Hawk, CO', ''), closest))
    for step in directions_result[0]['legs'][0]['steps']:
        html = step['html_instructions']
        html = re.sub(r'<div.+?>', '\n', html)
        html = re.sub(r'<.+?>', '', html)
        html = re.sub(r'^', '\t', html)
        html = re.sub(r'\n', '\n\t', html)
        #print(htmlp.html2text(html)
        print(html)

