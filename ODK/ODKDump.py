#!/usr/bin/python3

# 
#   Copyright (C) 2017, 2018   Free Software Foundation, Inc.
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

from sys import argv
import os
import sys
sys.path.append(os.path.dirname(argv[0]) + '../osmpylib')
sys.path.append(os.path.dirname(argv[0]) + 'osmpylib')
import xmltodict
import getopt
import glob
import odk
import ODKForm
# import gisnode
from osm import osmfile
import csv
#import kml
import logging
from fastkml import kml
#from shapely.geometry import Point, LineString, Polygon
import epdb                      # FIXME: remove later


def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result

class config(object):
    """Config data for this program."""
    def __init__(self, argv):
#        if len(argv) <= 1:
#            self.usage(argv)
            
        file = os.getenv('HOME') + "/.gosmrc"
        try:
            gosmfile = open(file, 'r')
        except Exception as inst:
            logging.warning("Couldn't open %s for writing! not using OSM credentials" % file)
            return

        # Default values for user options
        self.options = dict()
        self.options['format'] = "osm"
        self.options['indir'] = os.getcwd()
        self.options['outdir'] = os.getcwd()
        self.options['logging'] = 0
        self.options['convfile'] = "odk.conv"
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
            if name == "infile":
                self.options['infile'] = value[:index - 1]
            if name == "outfile":
                self.options['outfile'] = value[:index - 1]
            if name == "filter":
                self.options['filter'] = value[:index - 1]
            if name == "convfile":
                self.options['convfile'] = value[:index - 1]

        # Process the command line arguments
        # default values
        if len(argv) <= 2:
            self.usage(argv)
        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,f:,v,c:",
                ["help", "format=", "outfile", "indir", "verbose", "convfile"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()
            
        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == '--format' or opt == '-f':
                self.options['format'] = val
                format = val
            elif opt == "--outdir" or opt == '-o':
                self.options['outdir'] = val
            elif opt == "--indir" or opt == '-i':
                self.options['indir'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['logging'] += 1
                logging.basicConfig(filename='odkdump.log',level=logging.DEBUG)
            elif opt == "convfile" or opt == '-c':
                self.options['convfile'] = val
                            
    def get(self, opt):
        try:
            return self.options[opt]
        except:
            return False
    
    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--format[-f]    output format [osm, kml, cvs] (default=osm)
\t--outdir(-o)    Output directory
\t--infile(-i)    Input directory containing forms,instances
\t--verbose(-v)   Verbosity level
\t--convfile(-c)  Conversion data file name

This program scans the top level directory for ODK data files as produced
by the ODKCollect app for Android. Each XLSForm type gets it's own output
file containing all the waypoints entered using that form.
        """)
        quit()

    def dump(self):
        logging.info("Dumping config")
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))

# The logfile contains multiple runs, so add a useful delimiter
logging.info("-----------------------\nStarting: %r " % argv)

# Process the command line arguments
args = config(argv)

topdir = args.get('indir')
#outdir = open(args.get('outdir'), 'w')

# if verbose, dump to the terminal as well as the logfile.
if args.get('verbose') == 1:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

#file = open("/work/Mapping/ODK/Test.xml")
#odkform = ODKForm.ODKForm()
#xmlfile = odkform.parse(file)
## print("HEAD: %r" % xmlfile['head'])
#print("BODY: %r" % xmlfile['body'])
#print("BASE: %r" % xmlfile['base'])
#print("FIELDS: %r" % xmlfile['fields'])
#print("NODESETS: %r" % xmlfile['nodesets'])

def parse(instance, form):
    with open(instance, 'rb') as file:
        fields = list()
        gps = list()
        alltags = list()
        xml = file.read(10000)  # Instances are small, read the whole file
        doc = xmltodict.parse(xml)
        try:
            field = doc['data']
        except:
            logging.warning("No data in this instance")
            return False
        #if form == 'TeaHouse':
        #    import pdb; pdb.set_trace()
        for field in doc['data']:
            if field == 'meta' or field == '@id':
                continue
            # print("FIELD = %r" % field)
            nodesets = form[1]['nodesets']
            # Get the type of this nodeset
            ftype = ""
            try:
                ftype = nodesets[field]
            except:
                pass
            # A Some field types contains multiple internal fields,
            # Location - latitude, longitude, altitude, accuracy
            #print("\tFTYPE = %r" % ftype)
            #print("\tFVAL = %r" % fval)
            #print("\tVALUE = %r" % doc['data'][field])
            if ftype == 'geopoint':
                gps = doc['data'][field].split(' ')
                #print("\tGPS: %r" % gps)
            elif ftype == 'string':
                #logging.debug("\tString: %r" % doc['data'][field])
                tmptag = osm.makeTag(field, doc['data'][field])
                if doc['data'][field] is not None: 
                    alltags.append(osm.makeTag(field, doc['data'][field]))
            elif ftype == 'int':
                number = doc['data'][field]
                #print('\tInt %r' % number)
                if number is not None:
                    alltags.append(osm.makeTag(field, number))
                    # Select fields usually are a yes/no.
            elif ftype == 'select':
                #print('\tMulti Select: %r' % str(doc['data'][field]))
                if doc['data'][field]:
                    for data in doc['data'][field].split(' '):
                        #print("DATA1: %r" % data)
                        tmptag = osm.makeTag(field, data)
                        #print("FOOOO1: %r" % tmptag)
                        if len(tmptag) > 0:
                            alltags.append(osm.makeTag(field, data))
            elif ftype == 'select1':
                #print('Select')
                if doc['data'][field]:
                    for data in doc['data'][field].split(' '):
                        #print("DATA2: %r" % data)
                        tmptag = osm.makeTag(field, data)
                        #print("FOOOO2: %r" % tmptag)
                        alltags.append(osm.makeTag(field, data))
                        #print("FIXME: %r" % (gps, field))

    ret = dict()
    ret['GPS'] = gps
    ret['TAGS'] = osm.cleanup(alltags)

    return ret
#                try:
#                    osm.node(gps[0], gps[1], alltags)
#                except:
#                    pass
# FIXME: CSV old hack, fix later
#             import pdb; pdb.set_trace()
#             elif outfile.tell() == 0:
#                 fields = list()
#                 for field in doc['data']:
#                     if field == 'meta' or field == '@id':
#                         continue
#                     fval = forms[form]
#                     nodesets = fval['nodesets']
#                     # Get the type of this nodeset
#                     try:
#                         ftype = nodesets[field]
#                     except:
#                         ftype = 'string'
#                         # A Some field types contains multiple internal fields,
#                         # Location - latitude, longitude, altitude, accuracy
#                     if ftype == 'geopoint':
#                         fields.append("latitude")
#                         fields.append("longitude")
#                         fields.append("altitude")
#                         fields.append("accuracy")
#                         if format == 'csv':
#                             outfile.write('"latitude","longitude","altitude","accuracy",')
#                         continue
#                     # elif ftype == 'string':
#                     else:
#                         if format == 'csv':
#                             outfile.write('"' + field + '",')
#                             fields.append(field)

# #                with open('/tmp/' + form + '.csv', 'w', newline='') as csvfile:
#                 if format == 'csv':
#                     csvf = csv.writer(csvfile, delimiter=',',
#                                       quotechar='"', quoting=csv.QUOTE_ALL)
#                     csvf.writerow(fields)
                    
#                     # Drop the trailing comma and add a newline to finish this entry
#                     outfile.seek(outfile.tell() - 1)
#                     outfile.write('\n')
#                     outs = list()
#             for field in doc['data']:
#                 if field == 'meta' or field == '@id':
#                     continue
#                 if format == 'kml':
#                     node = kml.Placemark(ns, 'id', 'name', 'description')
                    
#                 fval = forms[form]
#                 nodesets = fval['nodesets']
#                 # Get the type of this nodeset
#                 try:
#                     ftype = nodesets[field]
#                 except:
#                     ftype = 'string'

#                 comma = ''
#                 if ftype == 'geopoint':
#                     gps = doc['data'][field].split(' ')
#                     for item in gps:
#                         if format == 'csv':
#                             outs.append(item)
#                             outfile.write('"' + item + '",')
#                         elif format == 'osm':
#                             osm.node(gps[0], gps[1])
#                     continue
#                 #elif ftype == 'string':
#                 else:
#                     if str(doc['data'][field]) == 'None':
#                         outfile.write(comma + '"",')
#                         outs.append('')
#                     else:
#                         outs.append(str(doc['data'][field]))
#                         outfile.write('"' + str(doc['data'][field]) + '",')
#                         # Numeric -
#                         #elif ftype == 'int':
#                         # Date -
#                         #elif ftype == 'date':
#                         # Time -
#                         #elif ftype == 'time':
#             csvf.writerow(outs)

#             # Terminate the line in the output file.
#             outfile.seek(outfile.tell() - 1)
#             outfile.write("\n")

formdir = topdir + '/forms'
try:
    odkdirs = os.listdir(formdir)
except:
    logging.error("%s doesn't exist!" % formdir)
    quit()

forms = dict()
odkform = ODKForm.ODKForm()
for file in odkdirs:
    try:
        fullfile = topdir + '/forms/' + file
        if os.path.isdir(fullfile):
            continue
        handle = open(fullfile)
        logging.info("Opened %s" % fullfile)
    except FileNotFoundError as e:
        logging.error("Can't open %s, %r" % (fullfile, e))

    name = file.replace(".xml","")
    xmlfile = odkform.parse(handle)
    forms[name] = xmlfile

current = ""
outfile = ""
outdir = args.get('outdir')
format = args.get('format')
fullpath = topdir + '/instances'
logging.info("Traversing " + fullpath + " recursively...")
out = ""
previous = ""
for form in forms.items():
    logging.info("Processing XForm %r" % form[0])
    #import pdb; pdb.set_trace()

    if format == 'osm':
        outfile = form[0]
        osm = osmfile(args, outdir + '/' + outfile)
        osm.header()
    # elif format == 'csv':
    #     csvfile = open('/tmp/' + form + '.csv', 'w', newline='')
    #     outfile = open(outdir + '/' + form + ".csv", 'w')
    # elif format == 'kml':
    #     ns = '{http://www.opengis.net/kml/2.2}'
    #     kmlfile = kml.KML()
    #     outfile = open(outdir + '/' + form + ".kml", 'w')

    pattern = fullpath + "/" + form[0] + "*"
    odkdirs = glob.glob(pattern)
    list.sort(odkdirs)
    for xmldir in odkdirs:
        logging.info("Opening directory " + xmldir)
        # FIXME: Ignore the *-media directories.
        #import pdb; pdb.set_trace()
        for xmlfile in glob.glob(xmldir + "/*.xml"):
            if os.path.isfile(xmlfile):
                logging.info("Opening XML file " + xmlfile)
                #import pdb; pdb.set_trace()
                data = parse(xmlfile, form)
                if data != False:
                    attrs = dict()
                    try:
                        attrs['lat'] = data['GPS'][0]
                        attrs['lon'] = data['GPS'][1]
                        attrs['ele'] = data['GPS'][2]
                        #osm.node(data['GPS'][0], data['GPS'][1], data['TAGS'])
                        osm.node(data['TAGS'], attrs)
                        #osm.node(data['TAGS'], attrs)
                    except:
                        logging.warning(" has no GPS coordinates")

    if format == 'osm':
        osm.footer()

        #d = kml.Document(ns, 'docid', 'doc name', 'doc description')
        #d.name = "bar"
        #kmlfile.append(d)
        #p = kml.Placemark(ns, 'id', 'name', 'description')
        # p.geometry =  Point(0.0, 0.0)
        #p.name = "foo"
        #kmlfile.append(p)
        #print(kmlfile.to_string(prettyprint=True))
        #gisnode = gisnode()



print("Input files in directory: %s/{forms,instances}" % args.get('indir'))
print("Output files in directory: %s" % outdir)
