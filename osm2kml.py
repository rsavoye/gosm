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
from osm import OverpassXAPI, osmConvert


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
        self.options['xapi'] = False
        self.options['database'] = None
        self.options['subset'] = None
        self.options['title'] = None
        self.options['remote'] = None
        self.options['infile'] = None
        self.options['outfile'] = "./out.kml"

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,s:,p:,t:,v,d:,r:,x,i:",
                ["help", "outfile", "subset", "poly", "title", "verbose", "database", "remote", "xapi", "infile"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--xapi" or opt == '-x':
                self.options['xapi'] = True
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
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

        # Setup default values
        self.base = "foo"
        if self.options['poly'] is None and self.options['infile'] is not None:
            self.base = os.path.basename(self.options['infile']).replace(".osm", "")
        elif self.options['poly'] is not None and self.options['infile'] is None:
            self.base = os.path.basename(self.options['poly']).replace(".poly", "")
        elif self.options['poly'] is None and self.options['infile'] is None and self.options['database'] is not None:
            self.base = self.options['database']
        elif self.options['poly'] is not None and self.options['infile'] is not None:
            # FIXME: run osmconvert to extract the subset of data
            self.base = os.path.basename(self.options['poly']).replace(".poly", "")
        elif self.options['poly'] is None and self.options['infile'] is None and self.options['database'] is None:
            logging.error("You to specify input data of some kind!")
            self.usage()
        else:
            logging.error("Need an input file or polygon!")

        if self.options['title'] is None:
            self.options['title'] = self.base

        if self.options['database'] is None:
            self.options['database'] = self.base

        logging.debug("Using %s as the base name" % self.base)

        # Have a canned subset collections
        if self.options['subset'] is not None:
            for sub in self.options['subset'].split(','):
                self.options[sub] = True
                if sub == 'rec':
                    self.options['trails'] = True
                    self.options['roads'] = True
                    self.options['camps'] = True
                    self.options['hotsprings'] = True
                if sub == 'ems':
                    self.options['addresses'] = True
                    self.options['trails'] = True
                    self.options['roads'] = True
                    self.options['milestones'] = True
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
        print("\tUsing '%s' as the default base name" % self.base)
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))

    # Basic help message
    def usage(self, argv=["osm2kml.py"]):
        print("This program downloads map tiles and the geo-references them")
        print(argv[0] + ": options:")
        print("""\t--help(-h)   Help
\t--outdir(-o)    Output file or directory for KML file(s)
\t--infile(-i)    An input file in OSM XML format
\t--poly(-p)      Input OSM polyfile to filter data
\t--subset(-p)    Subset of data to map
\t--title(-t)     Title for KML file
\t--database(-d)  Database to Use
\t--remote(-r)    Database Server to Use (default localhost)
\t--xapi(-x)      Download OSM data only
\t--verbose(-v)   Enable verbosity

Either an input file in osm xml format or a database name. If both are supplied,
the OSM file is imported into the database. To use fresh downloaded data
instead of the input file, use -x.
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

poly = dd.get('poly')
title = dd.get('title')
outfile = dd.get('outfile')
infile = dd.get('infile')
dbname = dd.get('database')

post = Postgis()
if dd.get('poly') is not None:
    polyfilter = Poly(poly)
    wkt = polyfilter.getWkt()
    # post.addPolygon(polyfilter)

if dd.get('xapi') is True:
    if dd.get('poly') is not None:
        # polyfilter = Poly()
        bbox = polyfilter.getBBox(poly)
        osm = outfile.replace('.kml', '.osm')
        xapi = OverpassXAPI(bbox, osm)
        if xapi.getData() is True:
            post.importOSM(osm, dbname)
        else:
            quit()
    else:
        logging.error("Need to specify a poly to download!")
        dd.usage()
elif infile is not None and dbname is not None and poly is None:
    post.importOSM(infile, dbname)
elif infile is not None and poly is not None:
    oc = osmConvert()
    osm = outfile.replace('.kml', '.osm')
    oc.applyPoly(poly, infile, osm)
    post.importOSM(osm, dbname)

print("------------------------")


#rr = post.getAddresses()
#print(len(rr))


# Create KML file
outkml = open(outfile, 'w')
mainkml = kml.KML()
ns = '{http://www.opengis.net/kml/2.2}'
mapstyle = MapStyle("ns='{http://www.opengis.net/kml/2.2}'")
mstyle = mapstyle.getStyles()
d = kml.Document(ns, 'docid', title, 'doc description')
# d = kml.Document(ns, 'docid', title, 'doc description', styles=mstyle)
mainkml.append(d)

#pdb.st()
#wkb = ppygis3.Geometry()

# Write buffer to KML file
#outkml = open(outfile, 'w')

post.connect('localhost', dbname)

# Get all of the cities and towns in the database. As some datasets
# (like fire_hydrants) are large, and at some zoom levels obscure
# details, these are put into a sub-folder in the KML file.
places = post.getPlaces(8)
# Get the bigger counties in the database.
counties = post.getPlaces(6)


#
# Hiking Trails
#
if dd.get('trails') is True:
    trails = post.getTrails()
    if trails is not None:
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
    else:
        logging.warning("No trails in thie database")

#
# Roads
#
threshold = 500
if dd.get('roads') is True:
    roads = post.getRoads()
    if roads is not None:
        f = kml.Folder(ns, 0, 'Roads', 'Roads in ' + title)
        if len(roads) > threshold:
            logging.info("%d roads, putting in separate file %s-roads.kml" % (len(roads), dbname))
            roadkml = kml.KML()
            # doc = kml.Document(ns, 'docid', title, 'doc description', styles=mstyle)
            doc = kml.Document(ns, 'docid', title, 'doc description')
            roadkml.append(doc)
        else:
            mainkml.append(f)

        for road in roads:
            if 'service' in road:
                if road['service'] == 'driveway':
                    # color =  mapstyle.driveways('driveway')
                    # description = "Private Driveway"
                    continue
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
            if len(roads) >= threshold:
                doc.append(p)
            else:
                f.append(p)

        if len(roads) >= threshold:
            roadout = open(dbname + "-roads.kml", 'w')
            roadout.write(roadkml.to_string(prettyprint=True))
            roadout.close()
    else:
        logging.warning("No roads in this database")

#
# House Addresses
#
threshold = 500
if dd.get('addresses') is True:
    addrs = post.getAddresses()
    if addrs is not None:
        f = kml.Folder(ns, 0, 'Addresses', 'House Addresses in ' + title)
        if len(addrs) >= threshold:
            logging.info("%d address, putting in separate file %s-addresses.kml" % (len(addrs), dbname))
            addrkml = kml.KML()
            # doc = kml.Document(ns, 'docid', title, 'doc description', styles=mstyle)
            doc = kml.Document(ns, 'docid', title, 'doc description')
            addrkml.append(doc)
        else:
            mainkml.append(f)

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
            if len(addrs) >= threshold:
                doc.append(p)
            else:
                f.append(p)

        if len(addrs) >= threshold:
            addrout = open(dbname + "-addresses.kml", 'w')
            addrout.write(addrkml.to_string(prettyprint=True))
            addrout.close()
    else:
        logging.warning("No addresses in this database")

#
# Mile Markers
#
if dd.get('milestones') is True:
    stones = post.getMilestones()
    if stones is not None:
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
    else:
        logging.warning("No milestones in this database")

#
# Landing Site
#
if dd.get('landingsite') is True:
    lzs = post.getLandingZones()
    if lzs is not None:
        f = kml.Folder(ns, 0, 'Landing Sites', 'Landing Sites in ' + title)
        d.append(f)
        for lz in lzs:
            style = mapstyle.landingzones(lz)
            p = kml.Placemark(ns, lz['osm_id'], lz['name'], style[1], styles=[style[0]])
            way = lz['wkb_geometry']
            p.geometry =  Point(way.geoms[0])
            f.append(p)
    else:
        logging.warning("No landing sites in this database")

#
# Hot Spring
#
if dd.get('hotsprings') is True:
    hsprings = post.getHotSprings()
    if hsprings is not None:
        f = kml.Folder(ns, 0, 'Hot Springs')
        d.append(f)
        for hs in hsprings:
            style = mapstyle.hotsprings(hs)
            p = kml.Placemark(ns, hs['osm_id'], hs['name'], style[1], styles=[style[0]])
            way = hs['wkb_geometry']
            p.geometry = Point(way.geoms[0])
            f.append(p)
    else:
        logging.warning("No Hot Springs in this database")

#
# Water Sources
#
if dd.get('firewater') is True:
    f = kml.Folder(ns, 0, 'Fire Water Sources')
    d.append(f)
    # cache the water sources we find in the place, so when we use
    # the county polygon, we don't create a duplicate Placemark.
    cache = dict()
    areas = list()
    areas = places
    areas += counties
    for place in areas:
        if 'osm_way_id' in place and place['osm_id'] is None:
            place['osm_id'] = place['osm_way_id']
        if place['place'] is None:
            if int(place['admin_level']) != 6:
                logging.warning("%s is missing the place tag, so will be ignored" % place['name'])
                continue
        elif place['place'] != 'city' and place['place'] != 'town' and place['name'] is not None:
            continue
        water = post.getFireWater(place['wkb_geometry'])
        # gging.debug("FIXME: %d in %s" % (len(water), place['name']))
        if place['name'] in cache:
            continue
        else:
            cache[place['name']] = place
        if len(water) > 0:
            nf = kml.Folder(ns, 0, '%s Water Sources' % place['name'])
            f.append(nf)
            for source in water:
                if source['osm_id'] in cache:
                    continue
                if 'name' not in source:
                    if 'ref' in source:
                        source['name'] = source['ref']
                    else:
                        source['name'] = "Unknown"
                way = source['wkb_geometry']
                cache[source['osm_id']] = source
                style = mapstyle.firewater(source)
                p = kml.Placemark(ns, source['osm_id'], source['name'], style[1], styles=[style[0]])
                p.geometry = Point(way.geoms[0])
                nf.append(p)
    else:
        logging.warning("No emergency water sources in this database")

#
# Campgrounds and camp sites
#
if dd.get('camps') is True:
    camps = post.getCampGrounds()
    if camps is not None:
        f = kml.Folder(ns, 0, 'Campgrounds')
        d.append(f)
        for camp in camps:
            if 'name' not in camp:
                if 'ref' in camp:
                    camp['name'] = camp['ref']
            nf = kml.Folder(ns, 0, camp['name'])
            f.append(nf)
            way = camp['wkb_geometry']
            for g in way.geoms:
                # FIXME: do we care ?
                if g.geom_type == 'Polygon':
                    style = mapstyle.campground(camp)
                    p = kml.Placemark(ns, camp['osm_id'], camp['name'], style[1], styles=[style[0]])
                    p.geometry = Polygon(g)
                    # continue
                sites = post.getCampSites(way[0])
                if sites is None:
                    continue
                for site in sites:
                    if 'openfire' in site or 'picnic_table' in site:
                        style = mapstyle.campsite(site, site['name'])
                    else:
                        style = mapstyle.campsite(camp, site['name'])
                    p = kml.Placemark(ns, site['osm_id'], site['name'], style[1], styles=[style[0]])
                    p.geometry = site['wkb_geometry'][0]
                    nf.append(p)
    else:
        logging.warning("No camps sites in this database!")

#
# Skiing
#
if dd.get('piste') is True:
    piste = post.getPiste()
    if piste is not None:
        f = kml.Folder(ns, 0, 'Ski Trails', 'Trails in ' + title)
        d.append(f)
        for trail in piste:
            #print(trail['name'])
            if trail['name'] is None:
                description = """OSM_ID: %s
                FIXME: this needs the real name!
                """ % trail['osm_id']
                trail['name'] = "Unknown: " + trail['osm_id']
                if 'piste:type' in trail:
                    m = re.search(".*nordic.*", trail['piste:type'])
                type = None
                if m is not None:
                    type = 'nordic'
                    m = re.search(".*downhill.*", trail['piste:type'])
                else:
                    type = 'downhill'
            style = mapstyle.piste(trail)
            p = kml.Placemark(ns, trail['osm_id'], trail['name'], style[1], styles=[style[0]])
            way = trail['wkb_geometry']
            p.geometry =  LineString(way.geoms[0])
            f.append(p)
    else:
        logging.warning("No skio trails in this database")

outkml.write(mainkml.to_string(prettyprint=True))
outkml.close()

# getIcons()
zip = zipfile.ZipFile("foo.kmz", mode="w")
x = np.array(mapstyle.getIcons())
for icon in np.unique(x):
    zip.write(icon)
zip.write(outfile)

logging.info("Wrote %s" % outfile)
