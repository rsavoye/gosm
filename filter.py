#!/usr/bin/python3

import os
import sys
import osmium
import logging
import getopt
import epdb
from haversine import haversine, Unit
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import osm
import psycopg2


if os.path.exists('filter.log'):
    os.remove('filter.log')

class myconfig(object):
    def __init__(self, argv=list()):
        # Default values for user options
        self.options = dict()
        self.options['verbose'] = False
        self.options['format'] = "osm"
        self.options['outfile'] = "reduced.osm"
        self.options['infile'] = None
        self.options['uid'] = ''
        self.options['user'] = ''

        # Read the config file to get our OSM credentials, if we have any
        file = os.getenv('HOME') + "/.gosmrc"
        try:
            gosmfile = open(file, 'r')
        except Exception as inst:
            logging.warning("Couldn't open %s for writing! not using OSM credentials" % file)
            return
        try:
            lines = gosmfile.readlines()
        except Exception as inst:
            logging.error("Couldn't read lines from %s" % gosmfile.name)

        for line in lines:
            try:
                # Ignore blank lines or comments
                if line is '' or line[1] is '#':
                    continue
            except Exception as inst:
                pass
            # First field of the CSV file is the name
            index = line.find('=')
            name = line[:index]
            # Second field of the CSV file is the value
            value = line[index + 1:]
            index = len(value)
#            print ("FIXME: %s %s %d" % (name, value[:index - 1], index))
            if name == "uid":
                self.options['uid'] = value[:index - 1]
            if name == "user":
                self.options['user'] = value[:index - 1]

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
threshold = 100

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
        dist = haversine(prev, cur, unit=Unit.METERS)
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

# This copies only nodes and ways with addr:housenumber set, but the distance
# calculation is ignoresd unless the input is sorted by geometry. That's hard
# to do, but easy in postgis.
if __name__ == '__main__':
    outfile = dd.get('outfile')
    osm = osm.osmfile(dd, outfile)
    osm.header()
    
    # if os.path.exists('copy.osm'):
    #    os.remove('copy.osm')
    # writer = osmium.SimpleWriter('copy.osm')
    # osm = OSMWriter(writer)
    # osm.apply_file("foo.osm", locations=True)
    # writer.close()

    # connect += " dbname='" + database + "'"
    connect = " dbname='TimberlineFireProtectionDistrict'" 
    dbshell = psycopg2.connect(connect)
    dbshell.autocommit = True
    dbcursor = dbshell.cursor()

    query = """DROP TABLE sorted;"""
    dbcursor.execute(query)
    logging.debug("Rowcount: %r" % dbcursor.rowcount)
    if dbcursor.rowcount < 0:
        logging.error("Query failed: %s" % query)

    # These first queries have no output, we're just sorting the data
    # internally using postgis into a new table,
    query = """SELECT "addr:housenumber",way INTO sorted FROM planet_osm_point WHERE "addr:housenumber" is not NULL ORDER BY way;"""
    dbcursor.execute(query)
    logging.debug("Rowcount: %r" % dbcursor.rowcount)
    if dbcursor.rowcount < 0:
        logging.error("Query failed: %s" % query)

    query = """SELECT ST_AsText(ST_Transform(way,4326)),"addr:housenumber" FROM sorted"""
    dbcursor.execute(query)
    logging.debug("Rowcount: %r" % dbcursor.rowcount)
    if dbcursor.rowcount < 0:
        logging.error("Query failed: %s" % query)

    result = dbcursor.fetchone()
    previous = None
    while result is not None:
        logging.debug(result)
        alltags = list()
        attrs = dict()
        lon = float(result[0].split()[0].replace("POINT(", ""))
        lat = float(result[0].split()[1].replace(")", ""))
        # Calculate the distance between points
        if previous is None:
            previous = (lat, lon)
        current = (lat, lon)
        dist = haversine(previous, current, unit=Unit.METERS)
        #logging.debug("DIST: %r" % dist)
        if dist < threshold:
            logging.info("Ignoring for dist %r" % dist)
            result = dbcursor.fetchone()
            continue
        previous = (lat, lon)

        # Make the OSM Node
        attrs['user'] = dd.get('user')
        attrs['uid'] = dd.get('uid')
        attrs['lon'] = str(lon)
        attrs['lat'] = str(lat)
        tagger = osm.makeTag('name', result[1])
        alltags.append(tagger)
        node = osm.node(alltags, attrs)
        result = dbcursor.fetchone()

    # query = """DROP TABLE sorted;"""
    # dbcursor.execute(query)
    # logging.debug("Rowcount: %r" % dbcursor.rowcount)
    # if dbcursor.rowcount < 0:
    #     logging.error("Query failed: %s" % query)

    # query = """SELECT "addr:housenumber",ST_Centroid(way) AS way INTO sorted FROM planet_osm_polygon WHERE "addr:housenumber" is not NULL;"""
    # dbcursor.execute(query)
    # logging.debug("Rowcount: %r" % dbcursor.rowcount)
    # if dbcursor.rowcount < 0:
    #     logging.error("Query failed: %s" % query)

    # query = """SELECT ST_Transform(way,4326),"addr:housenumber" FROM sorted;"""
    # dbcursor.execute(query)
    # logging.debug("Rowcount: %r" % dbcursor.rowcount)
    # if dbcursor.rowcount < 0:
    #     logging.error("Query failed: %s" % query)

    # result = dbcursor.fetchone()
    # while result is not None:
    #     logging.debug(result)
    #     result = dbcursor.fetchone()

    osm.footer()
