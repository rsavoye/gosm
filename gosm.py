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

import shapefile
import ogr
import gosm
import osm
import sys
import getopt
import cgi

class shpfile(object):
    """Hold data for an ERSI Shapefile shape."""
    def __init__(self, options):
        self.options = options
        
    def open(self, file):
        # self.shp="/work/Mapping/Utah/ArchaeologySites/ArchaeologySites.shp"
        # sf = shapefile.Reader("/work/Mapping/Utah/Trailheads/Trailheads.shp")
        self.shp = open(file, "rb")
        index = file.find('.')
        base = file[:index]
        shp = open(base + ".shp", "r")
        dbf = open(base + ".dbf", "r")
#        print (shp)
#        print (dbf)
        self.sf = shapefile.Reader(file)
#        self.sf = shapefile.Reader(shp=shp, dbf=dbf)
        self.fields = self.sf.fields
        self.shapeRecs = self.sf.shapeRecords()
        
    def dump(self):
        print (self.sf.fields)

        self.shapes = self.sf.shapes
        silly = sys.stdout
        print("Fields in: %r" % self.shp.name)
        for field in self.fields:
            silly.write(" '%s' " % field[0])
        silly.write("\n")
        shapeRecs = self.sf.iterShapeRecords()
        for entry in shapeRecs:
            end = (len(entry.record))
            for record in entry.record[:end]:
                try:
                    if record.isspace() == True:
                        silly.write(" 'ignore' ")
                    else:
                        silly.write(" %r " % record)
                except:
                    print (" '%r' " % record)
                    continue
                silly.write("\n")
            return

    def makeOSM(self, osm):
        silly = sys.stdout
        osm.header()
        shapeRecs = self.sf.iterShapeRecords()
        silly.write ("   Processing OSM file: \r")
        for entry in shapeRecs:
            end = (len(entry.record))
            tags = dict()

            # Process the tags for this record
            i = 1
            for record in entry.record[:end]:
                try:
                    if record.isspace() == True:
#                        print ("SPACE: %r" % record)
                        i = i + 1
                        continue
                    else:
                        # FIXME: remove embedded ', and &
                        bbb = str(record)
                        s = bbb.replace("&", "&amp;")
                        s = s.replace("'", "")
                        tags[self.fields[i][0]] = cgi.escape(s)
#                        print ("TEXT: %s %s" % (self.fields[i][0], record))
                except:
#                    print ("FLOAT %r" % (record))
                    i = i + 1
                    continue  
                i = i + 1
                # print a rotating character, so we know it's working
            rot = ("|", "/", "-", "\\", "*")

            k = 0
            refs = []
            for point in entry.shape.points:
#                print ("%r: %r" % (entry.record[1:2], point))
                lon = point[0]
                lat = point[1]
                node = osm.node(lat, lon, tags)
                refs.append(node)
                silly.write ("   Processing OSM file: %s\r" % rot[k])
                if k <= 3:
                    k = k + 1
                else:
                    k = 0
#                print("OSM ID: %r %r %r" % (tags, lat, lon))

            osm.way(refs, tags)
        osm.footer()

    def makeKML(self, kml):
        kml.header('FOObar')
        # FIXME:
        kml.footer()
        print("Unimplemented")
        
    def readShapes(self):
         shapeRecs = self.sf.iterShapeRecords()
         for entry in shapeRecs:
#             print ("BAR: %s, %s, %s" % (entry.record[1:3], entry.record[4:6], entry.record[7:9]))
             print (len(entry.shape.parts))
             print (len(entry.shape.points))
             for point in entry.shape.points:
                 print ("%r: %r" % (entry.record[1:2], point))
                
#             print ("BAR: %r " % entry.record[1:2])
             
    def readRecords(self):
        print ("Records: %d" % len(self.sf.records()))
        for record in (self.sf.iterRecords()):
            foo = self.createFields(record)
            print ("------------------------- ")
            for i,j in foo.items():
                print ("FIXME: %s"  % i, j)

            print ("=====================")
        
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
#            print ("FOOOOO %s %s %d" % (entry, field, i))
            columns[field] = entry
            i = i + 1

#        print (columns)
        return columns
        
class config(object):
    """Config data for this program."""
    def __init__(self, argv):
        # Read the config file to get our OSM credentials, if we have any
        file = "/home/rob/.gosmrc"
        try:
            gosmfile = open(file, 'r')
        except:
            print ("""WARNING: Couldn't open %s for writing! not using OSM credentials
            """ % file)
            return

        # Default to no credentials
        self.options = dict()
        self.options['user'] = ""
        self.options['uid'] = 0
        self.options['dump'] = False
        try:
            lines = gosmfile.readlines()
        except:
            print("ERROR: Couldm't read lines from %s" % gosmfile.name)
            
        for line in lines:
            if line[1] == '#':
                continue
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

        # Process the command line arguments
        # default values
        self.options['format'] = "osm"
        try:
            (opts,val) = getopt.getopt(argv[1:], "h,f:d", ["help","format=","user=","uid=","dump"])
        except getopt.GetoptError:    
            print('Invalid arguments.')
            
        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == '--format' or opt == '-f':
                self.options['format'] = val
                format = val
            elif opt == "--user":
                self.options['user'] = val
            elif opt == "--uid":
                self.options['uid'] = val
            elif opt == "--dump" or opt == '-d':
                self.options['dump'] = True
                            
    def get(self, opt):
        return self.options[opt]
    
    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--format[-f] output format (default=osm)
\t--user       OSM User name (optional)
\t--uid        OSM User ID (optional)
        """)
        quit()

    def dump(self):
        print ("Dumping config")
        for i,j in self.options.items():
            print("\t%s: %s" % (i, j))

class datafile(object):
    """Data file for the conversion"""
    def __init__(self):
        self.table = dict()
#        self.file = open(file, "r")

    def open(self, file):
        self.file = open(file, "r")
#        print ("FILE: %r" % self.file)

    def read(self):
        lines = self.file.readlines()
        for line in lines:
            if line[1] == '#':
                continue
            # First field of the CSV file is the name
            index = line.find(',')
            name = line[:index]
            # Second field of the CSV file is the value
            value = line[index + 1:]
            self.table[name] = value

#            print (self.table)
    def match(self, instr):
        return self.table[instr]
            
# Create an OSM tag
def createOSMTags( tag ):
    print("Unimplemented")
    tags = dict()
    # bicycle
    # mtn:scale:imba
    # access
    # sac_scale
    tags['TrailID'] = 'trailid'
    tags['SystemName'] = 'systemname'
    tags['Status'] = 'status'
    tags['Designated'] = 'designated'
    tags['MotorizedP'] = 'motorizedp'
    tags['PrimaryMai'] = 'primarymail'
    tags['TrailClass'] = 'trailclass'
    tags['TransNetwo'] = 'transnetwork'
    tags['ADAAccessi'] = 'adaaccess'
    tags['BikeDiffic'] = 'mtb:scale:imba'
    tags['HikeDiffic'] = 'sac_scale'
    tags['RoadConcur'] = 'roadconcur'
    tags['InfoURL'] = 'infourl'
    tags['Comments'] = 'comments'
    tags['TagsSource'] = 'tagssource'
    tags['LastUpdate'] = 'lastupdate'
    tags['CartoCode'] = 'cartocode'
    tags['SHAPE_Leng'] = 'leng'

    return tags
    
def createOSMColumn( field ):
    data = dict()
    
    data['PrimaryNam'] = 'name'
    data['Descriptio'] = 'highway'
    data['SurfaceTyp'] = 'surface'
    data['OtherRestr'] = 'access'

#    print (data)
#    for i in data:
#        print (i)
        
    return data
    print("Unimplemented")

