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

# import ogr
import gosm
# import osm
import shapefile
import sys


# This class holds a field from the Shapefile. It has 4 fields.
# Name - name of the field
# Type - character, Numbers, Longs, Dates
# Length - length of the field
# Decimals - number of decimals after the dot
class shpField(object):
    def __init__(self, field):
        self.field = field

    def getName(self):
        return self.field[0]

    def getType(self):
        return self.field[1]

    def isanum(self):
        if self.field[1] == 'N':
            return True
        else:
            return False

    def isalpha(self):
        if self.field[1] == 'C':
            return True
        else:
            return False

    def islong(self):
        if self.field[1] == 'L':
            return True
        else:
            return False

    def isdate(self):
        if self.field[1] == 'D':
            return True
        else:
            return False

    def getLength(self):
        return self.field[2]

    def getDecimals(self):
        return self.field[3]

        
class shpfile(gosm.verbose):
    """Hold data for an ERSI Shapefile shape."""
    def __init__(self, options):
        self.options = options
        gosm.verbose.__init__(self, options)
        
    def open(self, file):
        self.shp = open(file, "rb")
        self.debug("Opened inut file: %s" % file)
        self.sf = shapefile.Reader(file)
#        self.sf = shapefile.Reader(shp=shp, dbf=dbf)
        self.fields = self.sf.fields
        self.shapeRecs = self.sf.shapeRecords()

    # Dump the contents of the Shapefile.
    def dump(self):
        print(self.sf.fields)

        self.debug("Dumping file: " + self.options.get('infile'))
        self.shapes = self.sf.shapes
        silly = sys.stdout
        print("Fields in: %r" % self.shp.name)
        for field in self.fields:
            silly.write(" '%s' " % field[0])
        silly.write("\n")
        shapeRecs = self.sf.iterShapeRecords()
        k = 0
        for entry in shapeRecs:
            end = (len(entry.record))
            for record in entry.record[:end]:
                try:
                    if record.isspace() is True:
                        silly.write(" 'blank' ")
                    else:
                        silly.write(" %r " % str(record))
                except:
                    print(" '%r' " % str(record))
                    continue
            silly.write("\n")

        return

    def makeCSV(self, csv):
        self.shapes = self.sf.shapes
        silly = sys.stdout
        print("%r," % self.shp.name)
        for field in self.fields:
            silly.write(" '%s,' " % field[0])
        silly.write("\n")
        shapeRecs = self.sf.iterShapeRecords()
        for entry in shapeRecs:
            end = (len(entry.record))
            for record in entry.record[:end]:
                try:
                    if record.isspace() is True:
                        silly.write(",' ")
                    else:
                        silly.write(", %r " % record)
                except:
                    print(" '%r' " % record)
                    continue
            silly.write("\n")
        return

    def makeOSM(self, osm):
        silly = sys.stdout
        osm.header()
        shapeRecs = self.sf.iterShapeRecords()
        silly.write("   Processing OSM file: \r")
        for entry in shapeRecs:
            end = (len(entry.record))
            tags = dict()

            # Process the tags for this record
            i = 1
            for record in entry.record[:end]:
                try:
                    if record.isspace() is True:
                        # print ("SPACE: %r" % record)
                        i = i + 1
                        continue
                    else:
                        # FIXME: remove embedded characters that
                        # cause trouble with XML parsers
                        s = str(record)
                        s = s.replace("&", "&amp;")
                        s = s.replace("'", "")
                        s = s.replace("<", "lt")
                        s = s.replace(">", "gt")
                        # tags[self.fields[i][0]] = cgi.escape(s)

                        tagger = osm.makeTag(self.fields[i][0], s)
#                        tagger = osm.makeTag(self.fields[i][0], record)
                        if len(tagger) > 0:
                        # print("TAGS: %r" % tagger)
                            tags[tagger[0][0]] = tagger[0][1]
                            # for tag in tagger:
                                # print("TAG1: %r %r" % (tag[0], tag[1]))
                                
                            self.debug("shpfile:makeOSM(tag=%r, value=%r" % (tagger[0][0], tagger[0][1]))
                except:
                    # print("FLOAT %r" % (record))
                    i = i + 1
                    continue  
                i = i + 1
                # print a rotating character, so we know it's working
            rot = ("|", "/", "-", "\\", "*")

            # Process all the points in the Shape file
            k = 0
            refs = []
            for point in entry.shape.points:
                # print("%r: %r" % (entry.record[1:2], point))
                lon = point[0]
                lat = point[1]
                node = osm.node(lat, lon, tags)
                refs.append(node)
                silly.write("   Processing OSM file: %s\r" % rot[k])
                if k <= 3:
                    k = k + 1
                else:
                    k = 0
                    # self.debug("OSM ID: %r %r %r" % (tags, lat, lon))

            osm.makeWay(refs, tags)
        osm.footer()

    def makeKML(self, kml):
        kml.header('FOObar')
        # FIXME:
        kml.footer()
        print("Unimplemented")
        
    def readShapes(self):
        shapeRecs = self.sf.iterShapeRecords()
        for entry in shapeRecs:
            print(len(entry.shape.parts))
            print(len(entry.shape.points))
            for point in entry.shape.points:
                print("%r: %r" % (entry.record[1:2], point))

    def readRecords(self):
        print("Records: %d" % len(self.sf.records()))
        for record in (self.sf.iterRecords()):
            foo = self.createFields(record)
            print("------------------------- ")
            for i, j in foo.items():
                print("FIXME: %s"  % i, j)

            print("=====================")
        
    # Create a dictionary to hold the record data
    def createFields(self, record):
        columns = dict()
        # print (record)
        # print (self.fields)
        i = 1
        for entry in record:
            try:
                field = self.fields[i][0]
            except:
                print("OOPS!")
            columns[field] = entry
            i = i + 1

        return columns
