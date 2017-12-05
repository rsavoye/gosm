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

# import ogr
import logging
import shapefile
import sys
import re


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

        
class shpfile(object):
    """Hold data for an ERSI Shapefile shape."""
    def __init__(self, options):
        self.options = options
        
    def open(self, file):
        logging.info("Opened shp input files: %s" % file)
        self.sf = shapefile.Reader(file)
        shpfile = file + ".shp"
        self.shp = open(shpfile, "rb")
        #dbffile = file + ".dbf"
        #self.dbf = open(dbffile, "rb")
        #self.sf = shapefile.Reader(shp=shpfile, dbf=dbffile)
        self.fields = self.sf.fields
        self.shapeRecs = self.sf.shapeRecords()

    # Dump the contents of the Shapefile.
    def dump(self):
        print(self.sf.fields)

        logging.info("Dumping file: " + self.options.get('infile'))
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
        logging.debug("%r," % self.shp.name)
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
                    logging.debug(" '%r' " % record)
                    continue
            silly.write("\n")
        return

    def makeOSM(self, osm):
        silly = sys.stdout
        osm.header()
        shapeRecs = self.sf.iterShapeRecords()
        silly.write("   Processing OSM file: \r")
        for entry in shapeRecs:
            alltags = list()
            end = (len(entry.record))
            tags = dict()

            i = 1
            matched = False
            for record in entry.record:
                pattern = self.options.get('filter')
                match = self.fields[i][0] + "=" + str(record)
                if pattern != '' and match !='':
                    m = re.search(pattern, match)
                    #logging.debug("RE.SEARCH: %r %r %r" % (pattern, match, m))
                    if m != None:
                        logging.debug("Matched!! %r" % pattern)
                        matched = True
                        break
                i = i + 1

            if matched == False and pattern != '':
                continue

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
                        # tags[self.fields[i][0]] = cgi.escape(s
                        tagger = osm.makeTag(self.fields[i][0], s)
                        #print("FIXME: tagger %r" % tagger)
                        # Some fields are ignored
                        try:
                            if tagger['Ignore'] == 'Ignore':
                                continue
                        except:
                            try:
                                if tagger['4wd_only'] == 'yes':
                                    tagger['highway'] = "track"
                            except:
                                pass
                            alltags.append(tagger)
#                        tagger = osm.makeTag(self.fields[i][0], record)
#                        if len(tagger) > 0:
#                            print("TAGS: %r" % tagger)
#                            tags[tagger[0][0]] = tagger[0][1]
#                            # for tag in tagger:
#                                # print("TAG1: %r %r" % (tag[0], tag[1]))

#                            logging.info("shpfile:makeOSM(tag=%r, value=%r" % (tagger[0][0], tagger[0][1]))
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
                    # logging.info("OSM ID: %r %r %r" % (tags, lat, lon))

            osm.makeWay(refs, alltags)

        osm.footer()

    def makeKML(self, kml):
        kml.header('TODO')
        # FIXME:
        kml.footer()
        logging.warning("Unimplemented")
        
    def readShapes(self):
        shapeRecs = self.sf.iterShapeRecords()
        for entry in shapeRecs:
            print(len(entry.shape.parts))
            print(len(entry.shape.points))
            for point in entry.shape.points:
                logging.debug("%r: %r" % (entry.record[1:2], point))

    def readRecords(self):
        logging.debug("Records: %d" % len(self.sf.records()))
        for record in (self.sf.iterRecords()):
            foo = self.createFields(record)
            logging.debug("------------------------- ")
            for i, j in foo.items():
                print("FIXME: %s"  % i, j)

            logging.debug("=====================")
        
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
                logging.error("OOPS!")
            columns[field] = entry
            i = i + 1

        return columns
