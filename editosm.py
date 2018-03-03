#!/usr/bin/python3

# 
#   Copyright (C) 2018   Free Software Foundation, Inc.
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

# This script is where you want to import data, but all the names are all in
# upper cases, which isn't appropriaye for OSM. This fixes addresses
# specifically and nothing else by just capitalizing he first letter of
# every word in the value, and expanding abbreviations for road types tp
# their full name.
import os
import sys
import re
import string
import logging
import getopt
import epdb

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
        self.options['outfile'] = "./out.osm"
        self.options['convfile'] = os.path.dirname(argv[0]) + "/default.conv"
        self.options['uid'] = ''
        self.options['user'] = ''

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
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='shp2map.log',level=logging.DEBUG)

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
\t--dump{-d)      Dump the Shape fields
\t--outfile(-o)   Output file name
\t--infile(-i)    Input file name
\t--verbose(-v)   Enable verbosity
        """)
        quit()


dd = myconfig(argv)
dd.dump()

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

try:
    filespec = dd.get('infile')
    file = open(filespec, "r")
except Exception as inst:
    print("Couldn't open file %s" % filespec)

infile = dd.get('infile')
outfile = dd.get('outfile')
mod = 'action="modifiy"'

#outfile = open(filespec, "w")

osmout = osm.osmfile(dd, outfile)
osmout.header()
abbrevs=(" Hwy", "Rd", "Ln", "Dr", "Cir", "Ave", "Pl", "Trl", "Ct")
fullname=(" Highway", "Road", "Lane", "Drive", "Circle", "Avenue", "Place", "Trail", "Court")

tag = dict()
attrs = dict()
doc = etree.parse(infile)
members = list()
modified = False
for docit in doc.getiterator():
    #print("TAG: %r" % docit.tag)
    if docit.tag == 'node':
        tags = list()
        for elit in docit.getiterator():
            for ref,value in elit.items():
                if ref == 'k':
                    k = value
                elif ref == 'v':
                    if k == 'addr:street' or k == 'addr:full':
                        v = string.capwords(value)
                        pattern = ""
                        i = 0
                        while i < len(abbrevs):
                            pattern = " " + abbrevs[i] + "$"
                            m = re.search(pattern, v, re.IGNORECASE)
                            if m is not None:
                                pattern = " " + abbrevs[i] + " "
                                newline = v[0:m.start()]
                                rest = ' ' + v[m.start() + len(abbrevs[i])+1:len(v)]
                                v = newline + ' ' + fullname[i] + rest.rstrip(' ')
                                modified = True
                                break
                            pattern = " " + abbrevs[i] + " "
                            m = re.search(pattern, v, re.IGNORECASE)
                            if m is not None:
                                newline = v[0:m.start()]
                                rest = ' ' + v[m.start() + len(abbrevs[i])+1:len(v)]
                                v = newline + ' ' + fullname[i] + rest
                                modified = True
                                break
                            i = i +1
                    else:
                        v = value

                    tag = osmout.makeTag(k, v)
                    #print("<tag k=\"%r\" v=\"%r\"/>" % (k, v))
                    tags.append(tag)
                    #print("MODIFIED: %r, %r, %r" % (v != value, v, value))
                    if v != value:
                        modified = True
                        attrs['action'] = 'modify'
                else:
                    attrs[ref] = value
        osmout.node(tags, attrs)
        attrs = dict()
    elif docit.tag == 'way':
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
                    v = value
                    tag = osmout.makeTag(k, v)
                    tags.append(tag)
                else:
                    attrs[ref] = value
        osmout.makeWay(refs, tags, attrs)

    elif docit.tag == 'bounds':
        pass
    elif docit.tag == 'member':
        # members = list()
        # for elit in docit.getiterator():
        #     for ref,value in elit.items():
        #         member = dict()
        #         print("MEMBER:  %r, %r" % (ref, value))
        #         member[ref] = value
        #         members.append(member)
        pass
    elif docit.tag == 'nd':
        # Don't need to do anything, handled by osm.py
        pass
    elif docit.tag == 'osm':
        pass
    elif docit.tag == 'relation':
        tags = list()
        attrs = dict()
        members = list()
        for elit in docit.getiterator():
            modified = False
            for ref,value in elit.items():
               # print("RELATION: %r %r" % (ref, value))                    
                if ref == 'type' or ref == 'ref' or ref == 'role':
                    member = dict()
                    member[ref] = value
                    members.append(member)
                    continue
                elif ref == 'k':
                    k = value
                    continue
                elif ref == 'v':
                    v = value
                    tag = osmout.makeTag(k, v)
                    tags.append(tag)
                else:
                    attrs[ref] = value
        osmout.makeRelation(members, tags, attrs)




osmout.footer()
