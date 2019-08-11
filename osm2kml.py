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
import re
from fastkml import kml, styles
from osgeo import ogr
#import shapely.wkt
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiPolygon, mapping
import zipfile
import numpy as np

from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from color import MapStyle
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
                logging.basicConfig(filename='osm2kml.log',level=logging.DEBUG)

        if self.options['title'] is None and self.options['poly'] is not None:
            self.options['title'] =  os.path.basename(self.options['poly']).replace(".poly", "")
        if self.options['subset'] is not None:
            for sub in self.options['subset'].split(','):
                self.options[sub] = True
                if sub == 'rec':
                    self.options['trails'] = True
                    self.options['roads'] = True
                    self.options['camps'] = True
                if sub == 'ems':
                    self.options['trails'] = True
                    self.options['roads'] = True
                    self.options['camps'] = True
                    self.options['firewater'] = True
                    self.options['landingsite'] = True

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
t--remote(-r)    Database Server to Use (default localhost)
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

if dd.get('poly') is not None:
    poly = Poly()
    bbox = poly.getBBox(dd.get('poly'))
    #logging.info("Bounding box is %r" % bbox)

    # XAPI uses:
    # minimum latitude, minimum longitude, maximum latitude, maximum longitude
    xbox = "%s,%s,%s,%s" % (bbox[2], bbox[0], bbox[3], bbox[1])
    #logging.info("Bounding xbox is %r" % xbox)

print("------------------------")
post = Postgis()
post.connect('localhost', dd.get('database'))

#rr = post.getAddresses()
#print(len(rr))


# Create KML file
outkml = open(outfile, 'w')
k = kml.KML()
ns = '{http://www.opengis.net/kml/2.2}'
mapstyle = MapStyle("ns='{http://www.opengis.net/kml/2.2}'")
mstyle = mapstyle.getStyles()
d = kml.Document(ns, 'docid', title, 'doc description', styles=mstyle)
k.append(d)

#pdb.st()
#wkb = ppygis3.Geometry()

# Write buffer to KML file
outkml = open(outfile, 'w')

#
# Hiking Trails
#
if dd.get('trails') is True:
    trails = post.getTrails()
    f = kml.Folder(ns, 0, 'Trails', 'Trails in ' + title)
    d.append(f)
    #print(len(trails))
    for trail in trails:
        #print(trail['name'])
        if trail['name'] is None:
            description = """OSM_ID: %s
            FIXME: this needs the real name!
            """ % trail['osm_id']
            trail['name'] = "Unknown: " + trail['osm_id']
        else:
            description = trail['name']
        style = mapstyle.trails(trail)
        p = kml.Placemark(ns, trail['osm_id'], trail['name'], style[1], styles=[style[0]])
        way = trail['wkb_geometry']
        p.geometry =  LineString(way.geoms[0])
        f.append(p)

#
# Roads
#
if dd.get('roads') is True:
    roads = post.getRoads()
    f = kml.Folder(ns, 0, 'Roads', 'Roads in ' + title)
    d.append(f)
    #print(len(trails))
    for road in roads:
        #print(road['name'])
        if 'service' in road:
            if road['service'] == 'driveway':
                color =  mapstyle.make_hex('driveway')
            description = "Private Driveway"
        else:
            if road['name'] is None:
                description = """OSM_ID: %s
                FIXME: this needs the real name!
                """ % road['osm_id']
                road['name'] = "Unknown: " + road['osm_id']
            else:
                description = road['name']

        style = mapstyle.roads(road)
        p = kml.Placemark(ns, road['osm_id'], road['name'], style[1], styles=[style[0]])
        way = road['wkb_geometry']
        p.geometry =  LineString(way.geoms[0])
        f.append(p)

#
# House Addresses
#
if dd.get('addresses') is True:
    addrs = post.getAddresses()
    f = kml.Folder(ns, 0, 'Addresses', 'House Addresses in ' + title)
    d.append(f)
    for addr in addrs:
        #print(trail['name'])
        num = "addr['addr_housenumber']"
        street = "addr['addr_street']"
        description = ""
        if 'name' in addr:
            name = addr['name']
        else:
            name = ""
            description = "{name}{num}{street}"

        style = mapstyle.addresses(addr)
        p = kml.Placemark(ns, addr['osm_id'], addr['addr_housenumber'], style[1], styles=[style[0]])
        way = addr['wkb_geometry']
        p.geometry =  Point(way.geoms[0])
        f.append(p)

#
# Mile Markers
#
if dd.get('milestone') is True:
    stones = post.getMilestones()
    f = kml.Folder(ns, 0, 'Mile Markers', 'Mile markers in ' + title)
    d.append(f)
    for mark in stones:
        num = mark['name']
        street = "mark['alt_name']"

        style = mapstyle.milestones(mark)
        p = kml.Placemark(ns, addr['osm_id'], num, style[1], styles=[style[0]])
        way = mark['wkb_geometry']
        p.geometry =  Point(way.geoms[0])
        f.append(p)

#
# Landing Site
#
if dd.get('landingsite') is True:
    lzs = post.getLandingZones()
    f = kml.Folder(ns, 0, 'Landing Sites', 'Landing Sites in ' + title)
    d.append(f)
    for lz in lzs:
        style = mapstyle.landingzones(lz)
        p = kml.Placemark(ns, lz['osm_id'], lz['name'], style[1], styles=[style[0]])
        way = lz['wkb_geometry']
        p.geometry =  Point(way.geoms[0])
        f.append(p)

#
# Water Sources
#
if dd.get('firewater') is True:
    districts = post.getFireWater()
    f = kml.Folder(ns, 0, 'Emergency Water Sources')
    d.append(f)
    for dist in districts:
        if 'name' not in dist:
            if 'ref' in dist:
                dist['name'] = dist['ref']
        nf = kml.Folder(ns, 0, dist['name'])
        f.append(nf)
        way = dist['wkb_geometry']
        for g in way.geoms:
            if g.geom_type == 'Polygon':
                style = mapstyle.firewater(dist)
                p = kml.Placemark(ns, dist['osm_id'], dist['name'], style[1], styles=[style[0]])
                p.geometry = Polygon(g)
                continue
            elif g.geom_type == 'Point':
                # The relation has no geometry of it's own. Use tmp to
                # avoid a double query to the database
                tmp = post.getWay(g)
                if len(tmp) == 0:
                    continue
                site = tmp[0]
                if 'ref' in site:
                    if site['ref'] is not None and 'tourism' in site:
                        site['name'] = "Site %s" % site['ref']
                    else:
                        site['name'] = site['ref']
                style = mapstyle.firewater(site)
                p = kml.Placemark(ns, site['osm_id'], site['name'], style[1], styles=[style[0]])
            p.geometry = Point(g)
            nf.append(p)


#
# Campgrounds and camp sites
#
if dd.get('camps') is True:
    camps = post.getCampGrounds()
    f = kml.Folder(ns, 0, 'Campgrounds')
    d.append(f)
    for camp in camps:
        if 'name' not in camp:
            if 'ref' in camp:
                camp['name'] = camp['ref']
        nf = kml.Folder(ns, 0, camp['name'])
        f.append(nf)
        print(camp)
        way = camp['wkb_geometry']
        for g in way.geoms:
            if g.geom_type == 'Polygon':
                style = mapstyle.campground(camp)
                p = kml.Placemark(ns, camp['osm_id'], camp['name'], style[1], styles=[style[0]])
                p.geometry = Polygon(g)
                continue
            elif g.geom_type == 'Point':
                site = post.getCamp(g)[0]
                if 'ref' in site:
                    if site['ref'] is not None:
                        site['name'] = "Site %s" % site['ref']
                style = mapstyle.campsite(site)
                p = kml.Placemark(ns, site['osm_id'], site['name'], style[1], styles=[style[0]])
            p.geometry = Point(g)
            nf.append(p)

outkml.write(k.to_string(prettyprint=True))
outkml.close()

# getIcons()
zip = zipfile.ZipFile("foo.kmz", mode="w")
x = np.array(mapstyle.getIcons())
for icon in np.unique(x):
    zip.write(icon)
zip.write(outfile)

