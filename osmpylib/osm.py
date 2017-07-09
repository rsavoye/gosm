
# 
#   Copyright (C) 2017   Free Software Foundation, Inc.
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

import os.path
import time
import logging
from datafile import convfile


class osmfile(object):
    """OSM File output"""
    def __init__(self, options):
        self.options = options
        #self.verbose.__init__(self, options)
        
        # Open the OSM output file
        file = "/tmp/foobar.osm"
        try:
            if os.path.isfile(file):
                self.file = open(file, 'w')
            else:
                self.file = open(file, 'x')
            logging.info("Opened output file: " + file)
        except:
            logging.error("Couldn't open %s for writing!" % file)

#         # Read the config file to get our OSM credentials, if we have any
#         file = "/home/rob/.gosmrc"
#         try:
#             gosmfile = open(file, 'r')
#         except:
#             print("""WARNING: Couldn't open %s for writing! not using OSM credentials
#             """ % file)
#             return

        self.version = 3
        self.visible = 'true'
        self.osmid = -30470

        # Read the conversion data
        file = self.options.get('convfile')
        if file != False:
            self.ctable = convfile(file)
            self.ctable.read()
            
    def open(self, file, shp):
        self.file = open(file, "w")
        self.shp = shp
        
    def header(self):
        self.file.write('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
        self.file.write('<osm version="0.6" generator="gosm 0.1" timestamp="2017-03-13T21:43:02Z">\n')

    def footer(self):
        self.file.write("</osm>\n")
        
    def node(self, lat="", lon="", tags=dict()):
        #        timestamp = ""  # LastUpdate
        timestamp = time.strftime("%Y-%m-%dT%TZ")
        self.file.write("    <node id='" + str(self.osmid) + "\' visible='true'")
        self.file.write(" version='1'")
        self.file.write(" timestamp='" + timestamp + "\'")
        self.file.write(" uid='" + str(self.options.get('uid')) + "'")
        self.file.write(" user='" + self.options.get('user') + "'")
        self.file.write(" lat='" + str(lat) + "\'" + " lon='" + str(lon) + "'>\n")
# Don't add tags to nodes for now
#        for name, value in tags.items():
#            if str(value)[0] != 'b':
#                self.file.write("        <tag k='" + name + "' v='" + str(value) + "' />\n")

# FIXME: Add as a default ?
#        self.file.write("<tag k='created_by' v='Gosm 0.1'/>\n")
#        self.file.write("<tag k='name' v='" + name + "'/>\n")

        self.file.write("    </node>\n")
        self.osmid = self.osmid - 1

        return self.osmid - 1

    # Here's where the fun starts. Read a field header from a Shape file,
    # which of course are all different. Make an attempt to match these
    # random field names to standard OSM tag names. Same for the values,
    # which for OSM often have defined ranges.
    def makeTag(self, field, value):
        # FIXME: remove embedded ', and &
        newval = str(value)
        newval = newval.replace("&", "&amp;")
        newval = newval.replace("'", "")
#        newval = cgi.escape(newval)
        tags = list()
        self.debug("OSM:makeTag(field=%r, value=%r)" % (field, newval))

        try:
            newtag = self.ctable.match(field)
        except:
            newtag = "MISSING: " + field

        # Some fields we ignore, so we don't pollute OSM with lots of meaningless
        # data.
        if newtag == 'Ignore':
            return tags

        if newval.find('BIKE') >= 0:
            newtag = 'bicycle'
            newval = 'yes'
            tag = (newtag, newval)
            tags.append(tag)

        # See if it's a hiking trail
        elif newval.find('HIKE') >= 0 or newval.find('WALKING') >= 0:
            newtag = 'highway'
            newval = 'path'    # or footway
            tag = (newtag, newval)
            tags.append(tag)

        # See if it's a horse trail
        elif newval.find('HORSE') >= 0:
            newtag = 'horse'
            newval = 'yes'
            tag = (newtag, newval)
            tags.append(tag)

        # See if it's an ATV trail
        elif newval.find('ATV') >= 0:
            newtag = 'atv'
            newval = 'yes'
            tag = (newtag, newval)
            tags.append(tag)
        else:
            newval = value
        try:
            newval = self.ctable.attribute(newtag, newval)
#            print("ATTRS: %r %r" % (newtag, newval))
            tag = (newtag, newval)
            tags.append(tag)
        except:
            pass                # newval = value

#        tag = (newtag, newval)
#        tags.append(tag)
#        print ("TAGS2: %r" % tags)
        return tags

    def makeWay(self, refs, tags):
        # self.debug("osmfile::way(refs=%r, tags=%r)" % (refs, tags))
        self.file.write("    <way id='" + str(self.osmid) +
                        "\' visible='true'")
        timestamp = time.strftime("%Y-%m-%dT%TZ")
        self.file.write(" version='1'")
        self.file.write(" timestamp='" + timestamp + "\'")
        self.file.write(" user='" + self.options.get('user') + "' uid='" +
                        str(self.options.get('uid')) + "'>'\n")

        # Each ref ID points to a node id. The coordinates is im the node.
        for ref in refs:
            # FIXME: Ignore any refs that point to ourself. There shouldn't be
            # any, so this is likely a bug elsewhere when parsing the geom.
            if ref == self.osmid:
                break
            self.file.write("        <nd ref='" + str(ref) + "' />\n")

        value = ""
        
        for name, value in tags.items():
            if str(value)[0] != 'b':
                self.file.write("        <tag k='" + name + "' v='" +
                                str(value) + "' />\n")
            
        self.file.write("    </way>\n")
        
