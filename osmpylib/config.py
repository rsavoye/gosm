# 
# Copyright (C) 2017, 2018, 2019, 2020   Free Software Foundation, Inc.
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

import os
import getopt
import logging


class config(object):
    """Config data for this program."""
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
        self.options['limit'] = 0
        self.options['format'] = "osm"
        self.options['filter'] = ""
        self.options['extra'] = ""
        self.options['user'] = ""
        self.options['uid'] = 0
        self.options['type'] = "line"
        self.options['dump'] = False
        self.options['verbose'] = False
        self.options['infile'] = os.path.dirname(argv[0])
        self.options['outdir'] = "/tmp/"
        self.options['outfile'] = self.options['outdir'] + "tmp." + self.options.get('format')
        self.options['convfile'] = os.path.dirname(argv[0]) + "/default.conv"

        if len(argv) <= 2:
            self.usage(argv)

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,f:,v,c:,d,e:,t:",
                ["help", "format=", "outfile", "infile", "verbose", "convfile", "dump", "extra", "type"])
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

    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--filter[-f]    Filter data by a field
\t--user          OSM User name (optional)
\t--uid           OSM User ID (optional)
\t--dump{-d)      Dump the Shape fields
\t--outfile(-o)   Output file name
\t--infile(-i)    Input file name
\t--convfile(-c)  Conversion data file name
\t--limit(-l)     Limit the output records
\t--verbose(-v)   Enable verbosity
\t--type(-t)      Type of data, (way,line)
        """)
        quit()

    def dump(self):
        logging.info("Dumping config")
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))
