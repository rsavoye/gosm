#!/usr/bin/python3

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

from sys import argv
import xmltodict
import getopt
import os
import odk


class config(object):
    """Config data for this program."""
    def __init__(self, argv):
#        if len(argv) <= 1:
#            self.usage(argv)
            
        # Default values for user options
        self.options = dict()
        self.options['format'] = "csv"
        self.options['indir'] = "/tmp/odk/instances"
        self.options['outdir'] = "/tmp/odk"

        # Process the command line arguments
        # default values
        try:
            print(argv)
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,f:",
                ["help", "format=", "outfile", "indir"])
        except getopt.GetoptError:
            print('Invalid arguments.')
            return
            
        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == '--format' or opt == '-f':
                self.options['format'] = val
                format = val
            elif opt == "--outfile" or opt == '-o':
                self.options['outdir'] = val
            elif opt == "--indir" or opt == '-i':
                self.options['indir'] = val
                            
    def get(self, opt):
        try:
            return self.options[opt]
        except:
            return False
    
    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--format[-f]  output format [osm, kml, cvs] (default=csv)
\t--outdir(-o)  Output directory
\t--infile(-i)  Input file name

This program scans the top level directory for ODK data files as produced
by the ODKCollect app for Android. Each XLSForm type gets it's own output
file containing all the waypoints entered using that form.
        """)
        quit()


# Process the command line arguments
args = config(argv)
# print(args)

topdir = args.get('indir')
# outfile = open(args.get('outfile'), 'w')

current = ""
outfile = ""
outdir = args.get('outdir')
print("Traversing " + topdir + " recursively...")
odkdirs = os.listdir(topdir)
list.sort(odkdirs)
for dir in odkdirs:
    instance = os.listdir(topdir + '/' + dir)
    for inst in instance:
        print("Opening XML file " + inst)
        index = inst.find('_')
        form = inst[:index]
        if form != current:
            current = form
            outfile = open(outdir + '/' + form + ".csv", 'w')

        with open(topdir + '/' + dir + '/' + inst, 'rb') as file:
            xml = file.read(10000)
#            print(xml)
            doc = xmltodict.parse(xml)
            # Write the field headers to the output file. We only do this
            # once, as the headers don't change as long as they used the
            # same version of the XLSform.
            if outfile.tell() == 0:
                for field in doc['data']:
                    # A Location field contains multiple internal fields,
                    # latitude, longitude, altitude, accuracy
                    if field == 'location' or field == 'coordinates':
                        outfile.write('"latitude","longitude","altitude","accuracy",')
                        continue
                        
                    if field == 'meta':
                        continue

                    outfile.write('"' + field + '",')
                # Drop the trailing comma and add a newline to finish this entry
                outfile.truncate(outfile.tell() - 1)
                outfile.write('\n')

            for field in doc['data']:
                if field == 'location' or field == 'coordinates':
                    gps = doc['data'][field].split(' ')
                    for item in gps:
                        outfile.write('"' + item + '",')
                    continue
                #import pdb; pdb.set_trace()
                if type(doc['data'][field]) is str:
                    print(field + ": " + doc['data'][field])
                    outfile.write('"' + doc['data'][field] + '",')

            outfile.truncate(outfile.tell() - 1)
            outfile.write('\n')

