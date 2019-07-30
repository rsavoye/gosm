#!/usr/bin/python3

# 
#   Copyright (C) 2019   Free Software Foundation, Inc.
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

# ogr2ogr -t_srs EPSG:4326 Roads-new.shp hwy_road_aerial.shp


import os
import sys
import logging
import getopt
import epdb
import ppygis3
from fastkml import kml
from osgeo import ogr
#import shapely.wkt
from shapely.geometry import Point, LineString, Polygon

from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from poly import Poly
from sql import Postgis


class myconfig(object):
    def __init__(self, argv=list()):
        # Read the config file to get our OSM credentials, if we have any
        file = os.getenv('HOME') + "/.gosmrc"
        try:
            gosmfile = open(file, 'r')
        except Exception as inst:
            logging.warning("Couldn't open %s for writing! not using OSM credentials" % file)
            return

        # Default values for user options
        self.options = dict()
        self.options['verbose'] = False
        self.options['poly'] = None
        self.options['database'] = None
        self.options['subset'] = None
        self.options['title'] = None
        self.options['remote'] = None
        self.options['outfile'] = "./out.kml"

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,s:,p:,t:,v,d:,r:",
                ["help", "outfile", "subset", "poly", "title", "verbose", "database", "remote"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--subset" or opt == '-s':
                self.options['subset'] = val
            elif opt == "--poly" or opt == '-p':
                self.options['poly'] = val
            elif opt == "--title" or opt == '-t':
                self.options['title'] = val
            elif opt == "--database" or opt == '-d':
                self.options['database'] = val
            elif opt == "--remote" or opt == '-r':
                self.options['remote'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='tiler.log',level=logging.DEBUG)

        if self.options['title'] is None and self.options['poly'] is not None:
            self.options['title'] =  os.path.basename(self.options['poly']).replace(".poly", "")

    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

    def dump(self):
        logging.info("Dumping config")
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))

    # Basic help message
    def usage(self, argv=["osm2kml.py"]):
        print("This program downloads map tiles and the geo-references them")
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--outdir(-o)    Output directory for KML file
\t--poly(-p)      Input OSM polyfile
\t--subset(-p)    Subset of data to map
\t--title(-t)     Title for KML file
\t--database(-d)  Database to Use
\t--remote(-r)    Database Server to Use (default localhost)
\t--verbose(-v)   Enable verbosity
        """)
        quit()

dd = myconfig(argv)
#dd.checkOptions()
dd.dump()
if len(argv) <= 2:
    dd.usage(argv)

# The logfile contains multiple runs, so add a useful delimiter
try:
    logging.info("-----------------------\nStarting: %r " % argv)
except:
    pass

# if verbose, dump to the terminal as well as the logfile.
if dd.get('verbose') == 1:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

title = dd.get('title')
outfile = dd.get('outfile')

poly = Poly()
bbox = poly.getBBox(dd.get('poly'))
#logging.info("Bounding box is %r" % bbox)

# XAPI uses:
# minimum latitude, minimum longitude, maximum latitude, maximum longitude
xbox = "%s,%s,%s,%s" % (bbox[2], bbox[0], bbox[3], bbox[1])
#logging.info("Bounding xbox is %r" % xbox)

print("------------------------")
post = Postgis()
post.connect('localhost', 'TimberlineFireProtectionDistrict')
#rr = post.getRoads()
#print(len(rr))

#rr = post.getAddresses()
#print(len(rr))

trails = post.getTrails()
print(len(trails))

k = kml.KML()
ns = '{http://www.opengis.net/kml/2.2}'
d = kml.Document(ns, 'docid', title, 'doc description')
k.append(d)

f = kml.Folder(ns, 0, 'Trails', 'Trails in ' + title)
d.append(f)

#pdb.st()
#wkb = ppygis3.Geometry()

for trail in trails:
    print(trail)
    #print(trail['name'])
    if trail['name'] is None:
        description = """OSM_ID: %s
        FIXME: this needs the real name!
        """ % trail['osm_id']
        trail['name'] = "Unknown: " + trail['osm_id']
    else:
        description = trail['name']

    if 'surface' in trail:
        description += "\nSurface: " + trail['surface']
    if 'sac_scale' in trail:
        description += "\nSac_scale: " + trail['sac_scale']
    if 'bicycle' in trail:
        description += "\nBicycle: " + trail['bicycle']
    if 'horse' in trail:
        description += "\nHorse: " + trail['horse']
    if 'atv' in trail:
        description += "\nAtv: " + trail['atv']
    if 'foot' in trail:
        description += "\nFoot: " + trail['foot']
    if 'access' in trail:
        description += "\nAccess: " + trail['access']
    if 'motor_vehicle' in trail:
        description += "\nMotor Vehicle: " + trail['motor_vehicle']

    p = kml.Placemark(ns, trail['osm_id'], trail['name'], description)
    way = trail['wkb_geometry']
    p.geometry =  LineString(way.geoms[0])
    f.append(p)
#print(k.to_string(prettyprint=True))

outkml = open(outfile, 'w')
outkml.write(k.to_string(prettyprint=True))
outkml.close()
