
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

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have tags signifying what type
# it is.

import gosm
import time

class osmfile(object):
    """OSM File output"""
    def __init__(self, options):
        self.options = options
        
        # Open the OSM output file
        file = "/tmp/foobar.osm"
        try:
            self.file = open(file, 'w')
        except:
            print ("ERROR: Couldn't open %s for writing!" % file)

#         # Read the config file to get our OSM credentials, if we have any
#         file = "/home/rob/.gosmrc"
#         try:
#             gosmfile = open(file, 'r')
#         except:
#             print ("""WARNING: Couldn't open %s for writing! not using OSM credentials
#             """ % file)
#             return

        self.version = 3
        self.visible = 'true'
        self.osmid = -30470

#         # Default to no credentials
#         self.user = ""
#         self.uid = 0
#         try:
#             lines = gosmfile.readlines()
#         except:
#             print("ERROR: Couldm't read lines from %s" % gosmfile.name)
            
#         for line in lines:
#             if line[1] == '#':
#                 continue
#             # First field of the CSV file is the name
#             index = line.find('=')
#             name = line[:index]
#             # Second field of the CSV file is the value
#             value = line[index + 1:]
#             index = len(value)
# #            print ("FIXME: %s %s %d" % (name, value[:index - 1], index))
#             if name == "uid":
#                 self.uid=value[:index - 1]
#             if name == "user":
#                 self.user=value[:index - 1]
            
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
        self.file.write("    <node id='" +  str(self.osmid) + "\' visible='true'")
        self.file.write(" timestamp='" + timestamp + "\'")
        self.file.write(" user='" + self.options.get('user') + "' uid='" + str(self.options.get('uid')) + "'")
        self.file.write(" lat='" + str(lat) + "\'" + " lon='" + str(lon) + "'>\n")
        for name, value in tags.items():
            if str(value)[0] != 'b':
                self.file.write("        <tag k='" + name + "' v='" + str(value) + "' />\n")
# FIXME: Add as a default ?
#        self.file.write("<tag k='created_by' v='Gosm 0.1'/>\n")
#        self.file.write("<tag k='name' v='" + name + "'/>\n")

        self.file.write("    </node>\n")
        self.osmid = self.osmid - 1

        return self.osmid - 1
        
    def process(self):
        self.shp.readShapes()

    def way(self, refs, tags):
        self.file.write("    <way id='" +  str(self.osmid) + "\' visible='true'")
        timestamp = time.strftime("%Y-%m-%dT%TZ")
        self.file.write(" timestamp='" + timestamp + "\'")
        self.file.write(" user='" + self.options.get('user') + "' uid='" + str(self.options.get('uid')) + "'>'\n")

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
                self.file.write("        <tag k='" + name + "' v='" + str(value) + "' />\n")
            
        self.file.write("    </way>\n")
        
