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

import getopt


class verbose(object):
    """Debugging support for this program."""
    def __init__(self, config):
        self.verbosity = config.get('debug')

    def toggle(self):
        if self.verbosity is False:
            self.verbosity = True
        else:
            self.verbosity = False

    def debug(self, msg):
        if self.verbosity is True:
            print(msg)

    def pdb(self):
        # import code
        # code.interact(local=locals())
        import pdb; pdb.set_trace()

        
    def value(self):
        return self.verbosity

class config(object):
    """Config data for this program."""
    def __init__(self, argv):
        if len(argv) <= 2:
            self.usage(argv)
            
        # Read the config file to get our OSM credentials, if we have any
        file = "/home/rob/.gosmrc"
        try:
            gosmfile = open(file, 'r')
        except:
            print("""WARNING: Couldn't open %s for writing! not using OSM credentials
            """ % file)
            return

        # Default values for user options
        self.options = dict()
        self.options['format'] = "osm"
        self.options['user'] = ""
        self.options['infile'] = ""
        self.options['outfile'] = "tmp.osm"
        self.options['uid'] = 0
        self.options['dump'] = False
        self.options['limit'] = 0
        self.options['debug'] = False
        self.options['convfile'] = "default.conv"
        try:
            lines = gosmfile.readlines()
        except:
            print("ERROR: Couldn't read lines from %s" % gosmfile.name)
            
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
            if name == "infile":
                self.options['infile'] = value[:index - 1]
            if name == "outfile":
                self.options['outfile'] = value[:index - 1]
            if name == "convfile":
                self.options['convfile'] = value[:index - 1]

        # Process the command line arguments
        # default values
        try:
            print(argv)
            (opts, val) = getopt.getopt(argv[1:], "h,f:,d,o:,i:,l:,v,c:",
                ["help", "format=", "user=", "uid=", "dump", "outfile", "infile", "limit", "verbose", "config"])
        except getopt.GetoptError:
            print('Invalid arguments.')
            return

            # import pdb; pdb.set_trace()
            
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
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--infile" or opt == '-i':
                self.options['infile'] = val
            elif opt == "--convfile" or opt == '-c':
                self.options['convfile'] = val
            elif opt == "--limit" or opt == '-l':
                self.options['limit'] = int(val)
            elif opt == "--verbose" or opt == '-v':
                self.options['debug'] = True
                            
    def get(self, opt):
        try:
            return self.options[opt]
        except:
            return False
    
    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--format[-f]  output format [osm, kml, cvs] (default=osm)
\t--user          OSM User name (optional)
\t--uid           OSM User ID (optional)
\t--dump{-d)      Dump the Shape fields
\t--outfile(-o)   Output file name
\t--infile(-i)    Input file name
\t--convfile(-c)  Conversion data file name
\t--limit(-l)     Limit the output records
\t--verbose(-v)   Enable verbosity
        """)
        quit()

    def dump(self):
        print("Dumping config")
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))

class datafile(object):
    """Data file for the conversion"""
    def __init__(self, file=""):
        self.table = dict()
        self.attrtable = dict()
        if file != "":
            self.open(file)

    def open(self, file):
        self.file = open(file, "r")

    def read(self):
        lines = self.file.readlines()
        curname = ""
        for line in lines:
            if line[0] == '#':
                continue
            # First field of the CSV file is the name
            tmp = line.split(',')
            type = tmp[0]
            try:
                name = tmp[1]
            except:
                name = 'unknown'
            # store so we know when a set of attributes changes
            tmptab = dict()
            if curname == name:
                self.attrtable[curname] = tmptab
            else:
                items = dict()
                curname = name
            try:
                value = tmp[2]
            except:
                value = ""

            if type == 'attribute':
                try:
                    attr = tmp[3].replace("\n", "")
                except:
                    attr = ""

                    # print("datafile:read(name=%r, value=%r, attr=%r) is attribute" % (name, value, attr))
                items[value] = attr
                self.attrtable[name] = items
            elif type == 'tag':
                # print("datafile:read(name=%r, value=%r) is tag" % (name, value.replace("\n", "")))
                self.table[name] = value.replace("\n", "")
            elif type == 'column':
                # print("datafile:read(name=%r, value=%r) i column" % (name, value.replace("\n", "")))
                self.table[name] = value.replace("\n", "")

    def attribute(self, name, attr):
        # print("datafile:attribute(%r) %r" % (name, attr))
        try:
            value = self.attrtable[name][attr]
            # print("VAL: %r" % value)
            return value
        except KeyError:
            # print("No VAL for: %r" % name)
            return attr

    def match(self, instr):
        return self.table[instr]
    
