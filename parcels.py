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

"""
This programs merges two data files together. The first one is an OSM
file of parcel boundaries, which usually includes no metadata. The
metadata is in another file, usually a CSV file. So this splices the
metadata from the CSV file into the OSM file.
"""

import os
import sys
import re
import string
import logging
import getopt
import pdb
import epdb
import csv
import correct
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')

import osm
from lxml import etree
from lxml.etree import tostring


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
        self.options['logging'] = True
        self.options['dump'] = False
        self.options['verbose'] = False
        self.options['infile'] = os.path.dirname(argv[0])
        self.options['outfile'] = "./out"

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,v,",
                ["help", "outfile", "infile", "verbose"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--infiles" or opt == '-i':
                self.options['infiles'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='parcels.log',level=logging.DEBUG)

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
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--user          OSM User name (optional)
\t--uid           OSM User ID (optional)
\t--dump{-d)      Dump the data
\t--outfile(-o)   Output file name
\t--infile(-i)    Input file name
\t--verbose(-v)   Enable verbosity
        """)
        quit()


dd = myconfig(argv)
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

outfile = dd.get('outfile')
mod = 'action="modifiy"'

#outfile = open(filespec, "w")

# There's two input files, one has the parcel boundaries, the
# other the metadata.
infiles = dd.get('infiles').split(',')
file = dict()
#import epdb;epdb.set_trace()
suffix = infiles[0].split('.')[1]
if suffix != "osm":
    logging.error("Not an OSM file!")
    quit()
suffix = infiles[1].split('.')[1]
if suffix != "csv":
    logging.error("Not an CSV file!")
    quit()

fix = correct.correct()
    
tag = dict()
members = list()
modified = False

osmout = osm.osmfile(dd, outfile)
osmout.header()

# Read the CSV file into a dictionary so we can access the data later
lines = dict()
with open(infiles[1], mode='r') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        #logging.debug("owner_name: %r" % row["owner_name"])
        #logging.debug("folio: %r" % row["folio"])
        #logging.debug("str: %r" % row["str"])
        #logging.debug("str_unit: %r" % row["str_unit"])
        #logging.debug("str_sfx: %r" % row["str_sfx"])
        #logging.debug("legalDscr: %r" % row["legalDscr"])
        #logging.debug("mailingAddr1: %r" % row["mailingAddr1"])
        lines[row["folio"]] = row
        line_count += 1
    print(f'Processed {line_count} lines.')

# These are the tags we put in the output file
process_tags = [ "owner_name", "mailingAddr1", "str_num", "str" ]
tag_name = { "owner_name":"name", "mailingAddr1":"addr:full", "str_num":"addr:housenumber", "str":"addr:street" }

doc = etree.parse(infiles[0])
for docit in doc.getiterator():
    #print("TAG: %r" % docit.tag)
    if docit.tag == 'way':
        refs = list()
        tags = list()
        attrs = dict()
        for elit in docit.getiterator():
            modified = False
            for ref,value in elit.items():
                if ref == 'ref':
                    refs.append(value)
                elif ref == 'k':
                    k = value
                    continue
                elif ref == 'v':
                    if k == 'name':
                        if (value in lines) is False:
                            tag = osmout.makeTag(k, newvalue)
                            tags.append(tag)
                            print("no data for %r" % value)
                            continue
                        print("got data for %r" % lines[value])
                        line = lines[value]
                        for key in process_tags:
                            newvalue = line[key]
                            newvalue = fix.alphaNumeric(newvalue)
                            newvalue = fix.abbreviation(newvalue)
                            #newvalue = fix.compass(newvalue)
                            newvalue = string.capwords(newvalue)
                            tag = osmout.makeTag(tag_name[key], newvalue)
                            tags.append(tag)
                else:
                    attrs[ref] = value
        osmout.makeWay(refs, tags, attrs)
    elif docit.tag == 'node':
        tags = list()
        attrs = dict()
        for elit in docit.getiterator():
            newvalue = ""
            for ref,value in elit.items():
                if ref == 'k':
                    k = value
                elif ref == 'v':
                    if k == 'name':
                        newvalue = value
                    else:
                        continue

                    #print("FIXME: %r %r" % (fix.ismodified(), value))
                    tag = osmout.makeTag(k, newvalue)
                    #print("<tag k=\"%r\" v=\"%r\"/>" % (k, v))
                    tags.append(tag)
                    #print("NO CHANGE %r: %r" % (k, v))
                    if fix.ismodified() is True:
                        attrs['action'] = 'modify'
                else:
                    attrs[ref] = value

        osmout.node(tags, attrs)
        #osmout.makeNode(refs, tags, attrs)
osmout.footer()
