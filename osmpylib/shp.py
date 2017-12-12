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
        logging.debug(self.sf.fields)

        logging.info("Dumping file: " + self.options.get('infile'))
        self.shapes = self.sf.shapes
        silly = sys.stdout
        logging.debug("Fields in: %r" % self.shp.name)
        for field in self.fields:
            silly.write(" '%s' " % field[0])
        silly.write("\n")
        shapeRecs = self.sf.iterShapeRecords()
        for entry in shapeRecs:
            end = (len(entry.record))
            for record in entry.record[:end]:
                try:
                    if record.isspace() is True:
                        silly.write(" 'blank' ")
                    else:
                        silly.write(" %r " % str(record).replace("\n", ""))
                except Exception as inst:
                    logging.debug(" '%r' " % str(record))
                    continue
            silly.write("===================================================================\n")

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
                except Exception as inst:
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
            pattern = self.options.get('filter')
            for record in entry.record:
                match = self.fields[i][0] + "=" + str(record)
                if pattern is not '' and match is not '':
                    m = re.search(pattern, match)
                    # logging.debug("RE.SEARCH: %r %r %r" % (pattern, match, m))
                    if m is not None:
                        # logging.debug("Matched!! %r" % pattern)
                        matched = True
                        break
                i = i + 1

            if matched is False and pattern is not '':
                continue

            routes = ['null', 'hiker', 'horse', 'bicycle', 'motorcycle', 'atv', '4wd_only']
            snow = ['null', 'hike', 'nordic', 'snowmobile']
            # Process the tags for this record
            hours = False
            i = 1
            for record in entry.record[:end]:

                try:
                    # logging.debug("RECORD: %r" % record)
                    # import pdb; pdb.set_trace()
                    if record[0] is "N" and record[1] is "/" and record[2] is "A":
                        # logging.debug("GOT ONE - N/A: %r" % record)
                        continue
                    if record.isspace() is True:
                        # logging.debug("SPACE: %r" % record)
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
                        # FIXME: name may end with ohv-atv or atv or ohv'
                        # tags[self.fields[i][0]] = cgi.escape(s)
                        # FIXME: fix so it honors Ignore!
                        if re.search("[0-9][0-9]/[0-9][0-9]\-", s) is not None:
                            # logging.debug("GOT A DATE RANGE: %r" % s)
                            # tagger = osm.makeTag(self.fields[i][0], "yes")
                            if hours is False:
                                tagger['opening_hours'] = s
                            hours = True

                        tagger = osm.makeTag(self.fields[i][0], s)
                        # logging.debug("FIXME: tagger[%r] %r" % (self.fields[i][0], tagger))

                        try:
                            if tagger['route'] is not '':
                                # logging.debug("ROUTE: %r" % tagger)
                                route = tagger['route']
                                del tagger['route']
                                k = 0
                                while k < len(route):
                                    x = routes[int(route[k])]
                                    # logging.debug("ROUTE: %r %r[%r]" % (route, x, k))
                                    tagger[x] = "yes"
                                    k = k + 1
                        except Exception as inst:
                            pass

                        try:
                            if tagger['piste'] is not '':
                                # logging.debug("ROUTE: %r" % tagger)
                                piste = tagger['piste']
                                del tagger['piste']
                                k = 0
                                while k < len(piste):
                                    x = snow[int(piste[k])]
                                    # logging.debug("SNOW: %r %r[%r]" % (route, x, k))
                                    tagger['route'] = "piste"
                                    tagger['piste:type'] = x
                                    k = k + 1
                        except Exception as inst:
                            pass

                        # Some fields are ignored
                        try:
                            if tagger['Ignore'] == 'Ignore':
                                continue
                        except Exception as inst:
                            # Some tags trigger other tags, which can't be
                            # handled by the conversion file without getting
                            # ugly
                            try:
                                if tagger['hiker'] == 'yes':
                                    tagger['highway'] = "footway"
                                    tagger['sac_scale'] = "mountain_hiking"
                            except Exception as inst:
                                pass
                            try:
                                if tagger['4wd_only'] == 'yes':
                                    tagger['highway'] = "track"
                                    # tagger['highway'] = "path"
                                    # tagger['smoothness'] = "very_bad"
                            except Exception as inst:
                                pass
                            alltags.append(tagger)
                except Exception as inst:
                    # logging.debug("FLOAT %r" % (record))
                    i = i + 1
                    continue  
                i = i + 1
                # logging.debug a rotating character, so we know it's working
            rot = ("|", "/", "-", "\\", "*")

            # Extra tags specified on the command line to add
            if self.options.get('extra') is not '':
                extra = self.options.get('extra').split('=')
                tagger[extra[0]] = extra[1]
                alltags.append(tagger)
            # Process all the points in the Shape file
            k = 0
            refs = []
            for point in entry.shape.points:
                # logging.debug("POINTS: %r: %r" % (entry.record[1:2], point))
                lon = point[0]
                lat = point[1]
                node = osm.node(lat, lon, tags)
                refs.append(node)
                silly.write("   Processing OSM file: %s\r" % rot[k])
                if k <= 3:
                    k = k + 1
                else:
                    k = 0
                    # logging.debug("OSM ID: %r %r %r" % (tags, lat, lon))
            # logging.debug("REFS %r" % refs)

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
            logging.debug(len(entry.shape.parts))
            logging.debug(len(entry.shape.points))
            for point in entry.shape.points:
                logging.debug("%r: %r" % (entry.record[1:2], point))

    def readRecords(self):
        logging.debug("Records: %d" % len(self.sf.records()))
        for record in (self.sf.iterRecords()):
            foo = self.createFields(record)
            logging.debug("------------------------- ")
            for i, j in foo.items():
                logging.debug("FIXME: %s"  % i, j)

            logging.debug("=====================")

    # Create a dictionary to hold the record data
    def createFields(self, record):
        columns = dict()
        # logging.debug (record)
        # logging.debug (self.fields)
        i = 1
        for entry in record:
            try:
                field = self.fields[i][0]
            except Exception as inst:
                logging.error("OOPS!")
            columns[field] = entry
            i = i + 1

        return columns
