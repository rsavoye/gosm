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

# This script is where you wat to import data, but all the names are all in
# upper cases, which isn't appropriaye for OSM. This fixes addresses
# specifically and nothing else by just capitalizing he first letter of
# every word in the value..
import os
import sys
import re
import string
import logging
import getopt
import epdb

from config import config
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')


class myconfig(config):
    def __init__(self, argv=list()):
        # Default values for user options
        self.options = dict()
        self.options['logging'] = True
        self.options['dump'] = False
        self.options['verbose'] = False
        self.options['infile'] = os.path.dirname(argv[0])
        self.options['outfile'] = "./out.osm"

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
            elif opt == '--filter' or opt == '-f':
                self.options['filter'] = val
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
            elif opt == "--extra" or opt == '-e':
                self.options['extra'] = val
            elif opt == "--type" or opt == '-t':
                if val == "way" or val == "line":
                    self.options['type'] = val
                else:
                    self.usage(argv)
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='shp2map.log',level=logging.DEBUG)
            elif opt == "--dump" or opt == '-d':
                self.options['dump'] = True
            elif opt == "convfile" or opt == '-c':
                self.options['convfile'] = val

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

filespec = dd.get('outfile')
outfile = open(filespec, "w")

type = ""
node = list()
start = False
modified =  False
ignore = False
handled = False
user = 'rsavoye'

# # Process the input file
# lines = file.readlines()
# lines = ""
# for line in lines:
#     # The header of all OSM files.
#     m = re.search("^<\?xml|<osm|<bounds", line)
#     if m is not None:
#         outfile.write(line)
#         continue
    
#     newline = line

#     m = re.search("<way id=\".*\">", line, re.IGNORECASE)
#     if m is not None:
#         ignore = True

#     m = re.search("</way>", line, re.IGNORECASE)
#     if m is not None:
#         ignore = False
            
#     m = re.search("<relation id=\".*\">", line, re.IGNORECASE)
#     if m is not None:
#         ignore = True

#     m = re.search("</relation>", line, re.IGNORECASE)
#     if m is not None:
#         ignore = False
            
#     if ignore is True:
#         outfile.write(line)
#         continue

#     m = re.search("<node id=", line, re.IGNORECASE)
#     if m is not None:
#         data = dict()
#         for field in line.split(' '):
#             item = field.split('=')
#             if len(item) == 2:
#                 data[item[0]] = item[1].rstrip("\n>/\"").strip("\"")
      
#     m = re.search("<node id=\".*\">", line, re.IGNORECASE)
#     if m is not None:
#         ignore = False
#         #print("NODE START: " + line)
#         start = True
#         type = ""
#         #node.append(line)

#     m = re.search("<way id=\".*\">", line, re.IGNORECASE)
#     if m is not None:
#         #print("NODE START: " + line)
#         start = True

#     length = len(line)
#     end = line.find(' v=')
#     sub = line[0:end]
#     tag = line[10:end - 1]
#     value = line[end + 4:length - 4]

#     if data['user'] == user:
#         value = string.capwords(line[end + 4:length - 4])
#         if value != line[end + 4:length - 4]:
#             modified = True
#             handled = False

#     # This tag is obsolete as of 2012
#     #m = re.search("tiger:name_type", line)

#     # Look for abbreviations and expand them
#     i = 0
#     pattern = ""
#     while i < len(abbrevs):
#         pattern = " " + abbrevs[i] + "[\" ]+"
#         m = re.search(pattern, line, re.IGNORECASE)
#         if m is not None:
#             newline = line[0:m.start()]
#             rest = ' ' + line[m.start() + 4:len(line)]
#             newline += ' ' + fullname[i] + rest
#             type = fullname[i]
#             modified = True
#             handled = False
#             break
#         i = i +1

#     # End of a multi-line node
#     m = re.search("</node>", line, re.IGNORECASE)
#     if m is not None:
#         #print("NODE END: %r" % type)
#         newline = "</node>"
#         start = False
        
#     # A single-line node
#     m = re.search("<node id=\".*\"/>$", line, re.IGNORECASE)
#     if m is not None:
#         outfile.write(line)
#         node = list()
#         continue

#     # These are the fields that need to have the capitalization
#     # adjusted. 
#     #if tag == "addr:street" or tag == "addr:full" and data['user'] == 'rsavoye':
#     try:
#         print("DATA %r" % data['action'])
#     except:
#         pass
    
#     if modified is True:
#         # Any modified node needs to have the action field set in the line.
#         #print("ADDR: %r" % line)
#         newline = sub + ' v="' + value + '\"/>\n'
#         if handled is False and len(node) > 0:
#             idx = node[0].rfind('>')
#             begin = node[0][0:idx]
#             node[0] = begin + " action=\"modify\">" + '\n'
#             handled = True
#             modified = False

#     node.append(newline)

#     # Write to the output file
#     if start is False:
#         modified = False
#         # print("BAR: %r" % len(node))
#         for i in node:
#             outfile.write(i)
#             handled = False
#             node = list()

# #except Exception as inst:
# #    print("Couldn't read lines from %s" % filespec)


# # http://docs.osmcode.org/pyosmium/latest/ref_osmium.html

import osmium as osmium

class AddressFilter(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.num_nodes = 0
        self.modified = False
        try:
            os.remove("/tmp/foo.osm")
        except:
            pass
        self.outfile = osmium.SimpleWriter("/tmp/foo.osm")

    def fix_address(self, data):
        # No tags
        if not data.tags:
            return data

        # First fix capitalization problems for these tags
        newtags = []
        newval = ""
        modified = False
        for tag in data.tags:
            newval = tag.v
            try:
                if tag.k == "addr:street" or tag.k == "addr:full":
                    newval = string.capwords(tag.v)
                    if newval != tag.v:
                        modified = True
                    # Look for abbreviations and expand them
                    abbrevs=(" Hwy", "Rd", "Ln", "Dr", "Cir", "Ave", "Pl", "Trl", "Ct")
                    fullname=(" Highway", "Road", "Lane", "Drive", "Circle", "Avenue", "Place", "Trail", "Court")
                        
                    i = 0
                    pattern = ""
                    while i < len(abbrevs):
                        pattern = " " + abbrevs[i] + "[$ ]"
                        m = re.search(pattern, newval, re.IGNORECASE)
                        if m is not None:
                            print("FIXME: %r" % newval)
                            newline = newval[0:m.start()]
                            rest = ' ' + newval[m.start() + 4:len(newval)]
                            newval = newline + ' ' + fullname[i] + rest
                            modified = True
                            break
                        i = i +1
                        print("FIXME2: %r, %r" % (newval, modified))
            except:
                pass
                    
            newtags.append((tag.k, newval))

        if modified is True:
            return data.replace(tags=newtags)
        else:
            return data
 
    def node(self, node): 
        #print(n)
        foo = self.fix_address(node)
        self.outfile.add_node(foo)

    def way(self, way):
        foo = self.fix_address(way)
        self.outfile.add_way(foo)

    def relation(self, rel):
        foo = self.fix_address(rel)
        self.outfile.add_relation(foo)

    def done(self):
        #self.outfile.apply_file("/tmp/fooby.osm")
        self.outfile.close()

#writer = osm.SimpleWriter('test.osm')
i = AddressFilter()
i.apply_file("/work/Mapping/gosm.git/test.osm", locations=True)

print("Number of nodes: %d" % i.num_nodes)
i.done()


# class MyNode(osm.Node):
#     """The mutable version of ``osmium.osm.Node``. It inherits all attributes
#        from osmium.osm.mutable.OSMObject and adds a `location` attribute. This
#        may either be an `osmium.osm.Location` or a tuple of lon/lat coordinates.
#     """

#     def __init__(self, base=None, location=None, **attrs):
#         OSMObject.__init__(self, base=base, **attrs)
#         if base is None:
#             self.location = location
#         else:
#             self.location = location if location is not None else base.location


# x = MyNode()

import osm
import config
from lxml import etree
from lxml.etree import tostring

outfile = "/tmp/foo.osm"
dd = config.config(argv)
dd.dump()
osm = osm.osmfile(dd, outfile)

osm.header()
tag = dict()
attrs = dict()
doc = etree.parse("/work/Mapping/gosm.git/test.osm")
for docit in doc.getiterator():
    if docit.tag == 'node':
        tags = list()
        for elit in docit.getiterator():
            for ref,value in elit.items():
                if ref == 'k':
                    k = value
                elif ref == 'v':
                    v = value
                    tag = osm.makeTag(k, v)
                    print("<tag k=\"%r\" v=\"%r\"/>" % (k, v))
                    tags.append(tag)
                else:
                    attrs[ref] = value
                    print("<NODE %r %r" % (ref, value))
            osm.node(attrs['lat'], attrs['lon'], tags)
                
    elif docit.tag == 'tag':
        for elit in docit.getiterator():
            for ref,value in elit.items():
                if ref == 'k':
                    k = value
                elif ref == 'v':
                    v = value
                    print("<tag k=\"%r\" v=\"%r\"/>" % (k, v))


osm.footer()
