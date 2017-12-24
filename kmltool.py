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

# This is a simple application to manipulate KML files, which is needed
# for some mapping mobile apps or other data processing.
import os
import sys
import epdb
import logging
import getopt
import re
from kml import kmlfile
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')


class config(object):
    """Config data for this program."""
    def __init__(self, argv=list()):
        # Default values for user options
        self.options = dict()
        self.options['logging'] = True
        self.options['operation'] = "split"
        self.options['verbose'] = False
        self.options['infiles'] = os.path.dirname(argv[0])
        self.options['outdir'] = "/tmp/"
        self.options['outfile'] = self.options['outdir'] + "tmp.kml"

        if len(argv) <= 2:
            self.usage(argv)

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,v,e:,j,s",
                ["help", "outfile", "infiles", "verbose", "extract"])
        except getopt.GetoptError as e:
            logging.error('%r' % e)
            self.usage(argv)
            quit()

        for (opt, val) in opts:
            if opt == '--help' or opt == '-h':
                self.usage(argv)
            elif opt == "--outfile" or opt == '-o':
                self.options['outfile'] = val
            elif opt == "--infiles" or opt == '-i':
                self.options['infiles'] = val
            elif opt == "--extract" or opt == '-e':
                self.options['operation'] = "extract"
            elif opt == "--join" or opt == '-j':
                self.options['operation'] = "join"
            elif opt == "--split" or opt == '-s':
                self.options['operation'] = "split"
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                logging.basicConfig(filename='kmltool.log', level=logging.DEBUG)

    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

    # Basic help message
    def usage(self, argv):
        print(argv[0] + ": options: ")
        print("""\t--help(-h)   Help
\t--split(-s)     Split KML folders into separate files
\t--jpin(-j)      Join KML files together
\t--extract(-e)   Extract a Folder from a KML file
\t--outfile(-o)   Output file name
\t--infiles(-i)   Input file name(s)
\t--verbose(-v)   Enable verbosity
        """)
        quit()

    def dump(self):
        logging.info("Dumping config")
        for i, j in self.options.items():
            print("\t%s: %s" % (i, j))


class kmltool(object):
    """KML Processing class."""
    def __init__(self, config):
        self.config = config
        self.file = False
        config.dump()

    # Split a KML file into separate files, one for each Folder. Maps.ME
    # doesn't support folders yet.
    def split(self):
        logging.debug("spit")
        try:
            files = self.config.get('infiles')
            self.file = open(files, "r")
        except Exception as inst:
            logging.error("Couldn't open %r: %r" % (files, inst))
            return

        # logging.debug a rotating character, so we know it's working
        rot = ("|", "/", "-", "\\", "*")
        k = 0
        stdout = sys.stdout

        lines = self.file.readlines()
        name = False
        schema = False
        style = False
        header = list()
        kkk = kmlfile()
        for line in lines:
            stdout.write("   Processing KML file: %s\r" % rot[k])
            if k <= 3:
                k = k + 1
            else:
                k = 0
            if line[0] == '#':
                continue

            if style is True:
                header.append(line)
            if schema is True:
                header.append(line)
                
            m = re.search(".*</Schema>.*", line)
            if m is not None:
                schema = False
                pass
            m = re.search(".*<Schema>.*", line)
            if m is not None:
                header.append(line)
                schema = True
                pass
            m = re.search(".*</Style>.*", line)
            if m is not None:
                style = False
                pass
            m = re.search(".*<Style>.*", line)
            if m is not None:
                header.append(line)
                style = True
                pass

            m = re.search(".*</Folder>.*", line)
            if m is not None:
                kkk.footer()
                continue

            m = re.search(".*<Folder>.*", line)
            if m is not None:
                name = True
                continue
            else:
                if self.file is not False:
                    kkk.write(line)

            if name is True:
                m = re.search(".*<name>.*</name>", line)
                if m is not None:
                    start = line.find(">") + 1
                    end = line.rfind("<")
                    folder = line[start:end]
                    name = False
                    print("Processing KML Folder " + folder)
                    kkk.open("/tmp/" + folder + ".kml")
                    kkk.header(folder)
                    kkk.write(str(header))

    def join(self):
        # Join multiple KML files into one big KML file
        logging.debug("join")

    def extract(self):
        # Extract one KML folder out of the KML file
        logging.debug("extract")
        
dd = config(argv)

kmltool = kmltool(dd)

op = dd.get('operation')
if op == "split":
    kmltool.split()
elif op is "join":
    kmltool.join()
elif op is "extract":
    kmltool.extract()

