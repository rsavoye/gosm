#!/usr/bin/python3

# 
#   Copyright (C) 2017, 2018, 2019   Free Software Foundation, Inc.
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
# for some mapping mobile apps or other data processing. This doesn't use
# fastkml, this is primarily a text processing application.

# What this script can do is slice and dice KML file. Split one big file
# into several using the <Folder> as the delimiter. Some mobile apps,
# like Maps.ME can't hande Folders yet. It can also combine multiple KML
# files into a single KML file. This can also extract <Placemark>s from
# a KML file, useful when you only need a few data elements.
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
        self.options['root'] = os.path.dirname(argv[0])
        self.options['infiles'] = os.path.dirname(argv[0])
        self.options['outdir'] = "/tmp/"
        self.options['title'] = ""
        self.options['outfile'] = self.options['outdir'] + "tmp.kml"

        if len(argv) <= 2:
            self.usage(argv)

        try:
            (opts, val) = getopt.getopt(argv[1:], "h,o:,i:,v,e:,j,s,d:,t:",
                ["help", "outfile", "infiles", "verbose", "extract", "directory", "title"])
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
                self.options['extract'] = val
            elif opt == "--join" or opt == '-j':
                self.options['operation'] = "join"
            elif opt == "--split" or opt == '-s':
                self.options['operation'] = "split"
            elif opt == "--directory" or opt == '-d':
                self.options['outdir'] = val
            elif opt == "--title" or opt == '-t':
                self.options['title'] = val
            elif opt == "--verbose" or opt == '-v':
                self.options['verbose'] = True
                with open('kmltool.log', 'w'):
                    pass
                logging.basicConfig(filename='kmltool.log', level=logging.DEBUG)
                root = logging.getLogger()
                root.setLevel(logging.DEBUG)

                ch = logging.StreamHandler(sys.stdout)
                ch.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                ch.setFormatter(formatter)
                root.addHandler(ch)

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
\t--extract(-e)   Extract a Placemarks from a KML file using regex
\t--outfile(-o)   Output file name
\t--infiles(-i)   Input file name(s)
\t--verbose(-v)   Enable verbosity
\t--title(-t)     Set output file title
        """)
        quit()

    def get(self, opt):
        try:
            return self.options[opt]
        except Exception as inst:
            return False

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
        """Split a KML file into separate files, one for each Folder"""
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
        kml = kmlfile()
        for line in lines:
            stdout.write("   Processing KML file: %s\r" % rot[k])
            if k <= 3:
                k = k + 1
            else:
                k = 0
            if line[0] == '#':
                continue

            # if style is True:
            #     header.append(line)
            # if schema is True:
            #     header.append(line)
                
            # m = re.search(".*</Schema>.*", line)
            # if m is not None:
            #     schema = False
            #     pass
            # m = re.search(".*<Schema>.*", line)
            # if m is not None:
            #     header.append(line)
            #     schema = True
            #     pass
            # m = re.search(".*</Style>.*", line)
            # if m is not None:
            #     style = False
            #     pass
            # m = re.search(".*<Style>.*", line)
            # if m is not None:
            #     header.append(line)
            #     style = True
            #     pass

            m = re.search(".*</Folder>.*", line)
            if m is not None:
                kml.footer()
                continue

            m = re.search(".*<Folder>.*", line)
            if m is not None:
                name = True
                continue
            else:
                if self.file is not False:
                    kml.write(line)

            if name is True:
                m = re.search(".*<name>.*</name>", line)
                if m is not None:
                    start = line.find(">") + 1
                    end = line.rfind("<")
                    folder = line[start:end]
                    name = False
                    logging.debug("Exporting KML Folder " + folder)
                    kml.open("/tmp/" + folder + ".kml")
                    kml.header(folder)
                    kml.styles(self.config.get('root') + '/styles.kml')
                    kml.write(header)

    def join(self):
        """Join multiple KML files into a singe KML file """
        logging.debug("join")
        out = kmlfile()
        name = self.config.get('outfile')
        out.open(name)
        name = os.path.basename(name.replace(".kml", ""))
        title = self.config.get('title')
        if title is None:
            title = name.capitalize()
        out.header(title)
        out.styles(self.config.get('root') + '/styles.kml')
        logging.info("Opened %r for KML output" % self.config.get('outfile'))
        # Each inpuot file becomes a KML Folder in the output file
        for file in self.config.get('infiles').split(','):
            name = os.path.basename(file.replace(".kml", ""))
            out.folderStart(name)
            try:
                self.file = open(file, "r")
                logging.info("Opened %r for KML input" % file)
            except Exception as inst:
                logging.error("Couldn't open %r: %r" % (file, inst))
                return
            start = False
            lines = self.file.readlines()
            for line in lines:
                m = re.search(" *<Placemark>", line)
                if m is not None:
                    start = True
                m = re.search(" *<Folder>", line)
                if m is not None:
                    start = True
                # End of the data we want
                m = re.search(" *</Document>", line)
                if m is not None:
                    break
                if start is True:
                    out.write(line)

            out.folderEnd()
            self.file.close()
        out.footer()

    def extract(self):
        # Extract one KML folder out of the KML file
        logging.debug("extract")
        out = kmlfile()
        name = self.config.get('outfile')
        out.open(name)
        name = os.path.basename(name.replace(".kml", ""))
        out.header(name.capitalize())
        out.styles(self.config.get('root') + '/styles.kml')
        logging.info("Opened %r for KML output" % self.config.get('outfile'))
        # Each inpuot file becomes a KML Folder in the output file
        for file in self.config.get('extract').split(','):
            pass
            try:
                self.file = open(self.config.get('infiles'), "r")
                logging.info("Opened %r for KML input" % file)
            except Exception as inst:
                logging.error("Couldn't open %r: %r" % (file, inst))
                return
            cache = list()
            match = False
            start = False
            folder = False
            lines = self.file.readlines()
            for line in lines:
                m = re.search(".*Folder>.*", line)
                if m is not None:
                    folder = True
                    # out.folderStart()
                m = re.search(" *<Placemark>.*", line)
                if m is not None:
                    if folder is True:
                        folder = False
                        cache.append(line)
                        start = True
                        continue
                    start = True
                    folder = False
                m = re.search(".*" + file + ".*", line)
                if m is not None:
                    match = True
                m = re.search(" *</Placemark>.*", line)
                if m is not None:
                    start = False
                    if match is True:
                        cache.append(line)
                        out.write(cache)
                        cache = list()
                        match = False
                    else:
                        cache = list()
                        match = False

                if start is True:
                    cache.append(line)

        # out.folderEnd()
        self.file.close()
        out.footer()

#epdb.set_trace()
dd = config(argv)

kmltool = kmltool(dd)

op = dd.get('operation')
if op == "split":
    kmltool.split()
elif op is "join":
    kmltool.join()
elif op is "extract":
    kmltool.extract()

