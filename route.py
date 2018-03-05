#!/usr/bin/python3

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
    destination = argv[1] + ", Black Hawk, CO"

stations = ["5927 Magnolia Road, Nederland, CO" ,"3999 Highway 72, Pinecliffe, CO", "135 Tolland Road, Rollinsville, CO", "448 Pine Dr., Black Hawk, CO","14908 Highway 119, Black Hawk, CO", "146 North Dory Lakes Drive, Black Hawk, CO", "660 Highway 46, Black Hawk, CO", "2236 Smith Hill Road, Golden, CO", "4611 Smith Hill Road, Golden, CO", "495 Apex Road, Black Hawk, CO"]

names = ["Station 1", "Station 2", "Station 3", "Station 4", "Station 5", "Station 6", "Station7 ", "Station8 ", "Station9 ", "Station 10"]

coordinates = ["39.9768221,-105.417122", "39.9392044,-105.4404452", "39.91756700000001,-105.505307", "39.89200400000001,-105.4813322", "39.864616,-105.4656415","39.8475062,-105.476561", "39.8400306,-105.4811873", "39.7445193,-105.229805", "39.82077049999999,-105.4081804", "39.8234031,-105.5235759"]

apikey="AIzaSyCuTm3ux305teZ2cz9AS-zAZlY0sZ1-U1w"

gmaps = googlemaps.Client(apikey)

now = datetime.now()
dest = gmaps.distance_matrix(stations, destination, mode="driving", units="imperial", departure_time=now)

data = dict()
addrs = dict()
i = 0
for row in dest['rows']:
    index = row['elements'][0]['distance']['text'].replace(' mi', '')
    data[index] = names[i]
    addrs[index] = stations[i]
    i += 1

best = 100.0
for k,v in data.items():
    distance = float(k)
    print("%r %r" % (best, distance))
    if  distance < best:
        best = distance


closest = data[str(best)]
print("FOO: " + closest)

print("Closest station is: %r, %r miles away" % (closest, best))
quit()

origin = addrs[sss[0]]

# Look up an address with reverse geocoding
geocode_result = gmaps.geocode('Boulder, CO')
lat = geocode_result[0]["geometry"]['location']['lat']
lng = geocode_result[0]["geometry"]['location']['lng']

reverse_geocode_result = gmaps.reverse_geocode((lat, lng))

# Request directions via public transit
here = gmaps.geolocate()
whereami = gmaps.reverse_geocode(here['location'])

directions_result = gmaps.directions(origin,
                                     destination,
                                     mode="driving",
                                     language=None,
                                     avoid=None,
                                     units="imperial",
                                     departure_time=now)

#pprint.pprint(directions_result)
#http://py-googlemaps.sourceforge.net/#googlemaps-methods

start = 'Constitution Ave NW & 10th St NW, Washington, DC'
end   = 'Independence and 6th SW, Washington, DC 20024, USA'
dirs  = gmaps.directions(start, end) 
#time  = dirs['Directions']['Duration']['seconds']
#dist  = dirs['Directions']['Distance']['meters']
#route = dirs['Directions']['Routes'][0]
htmlp = html2text
for step in directions_result[0]['legs'][0]['steps']:
    html = step['html_instructions']
    html = re.sub(r'<div.+?>', '\n', html)
    html = re.sub(r'<.+?>', '', html)
    #print(htmlp.html2text(html)
    print(html)
