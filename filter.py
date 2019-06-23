#!/usr/bin/python3

import os
import sys
import osmium
import logging
import getopt
import epdb
#from haversine import haversine, Units
import haversine
import csv
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')


if os.path.exists('filter.log'):
    os.remove('filter.log')

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
        self.options['format'] = "osm"
        self.options['outfile'] = "reduced.osm"
        self.options['infile'] = None

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,v,f:",
                ["help", "outfile", "infile", "verbose", "format"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val

            elif opt == "--format" or opt == '-f':
                self.options['format'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='filter.log',level=logging.DEBUG)


    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

    def dump(self):
        logging.info("Dumping config")
        for i, j in self.options.items():
            logging.debug("\t%s: %s" % (i, j))

    # Basic help message
    def usage(self, argv=["filter.py"]):
        logging.debug("This program filters addresses by distance for use in a VRT")
        logging.debug(argv[0] + ": options:")
        logging.debug("""\t--help(-h)   Help
\t--outfile(-o)    Output file
\t--infile(-i)    Input file
\t--format(-f)    Output file format, (csv, osm)
\t--verbose(-v)   Enable verbosity
        """)
        quit()

dd = myconfig(argv)
#dd.dump()
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


# distance between points
threshold = 30

# https://gdal.org/drivers/vector/csv.html
# Latitude,Longitude,Name
# 48.1,0.25,"First point"
# 49.2,1.1,"Second point"
# 47.5,0.75,"Third point"


def distance(previous, current):
    if previous is not None:
        prev = (previous.location.lat, previous.location.lon)
    else:
        if current is None:
            return 0.0
        else:
            prev = (current.location.lat, current.location.lon)
    cur = (current.location.lat, current.location.lon)
    if prev is not None and current is not None:
        dist = haversine.haversine(prev, cur, unit=haversine.Unit.METERS)
    else:
        dist = 0.0
    logging.debug("DIST: %r" % dist)

    return dist
    

class OSMWriter(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer
        self.previous = None
        
    def node(self, node):
        # if node.get('addr:housenumber') is not None:
        logging.debug("NODE TAGS: %r" % node)
        # logging.debug("NODE TAGS %r" % node.tags.get('addr:housenumber'))
        dist = distance(self.previous, node)
        if dist > threshold or dist == 0.0:
            self.writer.add_node(node)
        self.previous = node

    def way(self, way):
        logging.debug("WAY TAGS: %r" % way)
        # FIXME: for now we only want ways that are house addressess,
        # which is when a building polygon has been tagged
        if way.tags.get('addr:housenumber') is not None:
            # logging.debug("WAY TAGS %r" % way.tags.get('addr:housenumber'))
            # dist = distance(self.previous, way)
            # self.previous = way
            # if dist > threshold or dist == 0.0:
            self.writer.add_way(way)

    def relation(self, n): 
        logging.debug("REL TAGS %s" % n.tags.get('addr:housenumber'))
        self.writer.add_relation(n)

if __name__ == '__main__':
    if os.path.exists('copy.osm'):
        os.remove('copy.osm')
    writer = osmium.SimpleWriter('copy.osm')
    n = OSMWriter(writer)
    n.apply_file("foo.osm", locations=True)
    writer.close()
