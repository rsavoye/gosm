
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

import os.path
import time
import logging
from datafile import convfile
import config
import html

class osmfile(object):
    """OSM File output"""
    def __init__(self, options, outfile=False):
        self.options = options
        #self.file = False
        # Read the config file to get our OSM credentials, if we have any
        # self.config = config.config(self.options)
        self.version = 3
        self.visible = 'true'
        self.osmid = -30470

        # Open the OSM output file
        if outfile == False:
            self.outfile = self.options.get('outdir') + "foobar.osm"
        try:
            if os.path.isfile(outfile):
                self.file = open(outfile, 'w')
            else:
                self.file = open(outfile, 'x')
            logging.info("Opened output file: " + outfile)
        except Exception as inst:
            logging.error("Couldn't open %s for writing!" % outfile)

        # This is the file that contains all the filtering data
        self.ctable = convfile(options.get('convfile'))

    def isclosed(self):
        return self.file.closed

    def header(self):
        if self.file != False:
            self.file.write('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
            #self.file.write('<osm version="0.6" generator="gosm 0.1" timestamp="2017-03-13T21:43:02Z">\n')
            self.file.write('<osm version="0.6" generator="gosm 0.1">\n')

    def footer(self):
        #logging.debug("FIXME: %r" % self.file)
        self.file.write("</osm>\n")
        if self.file != False:
            self.file.close()

    def makeNode(self, attr=dict()):
        node(attr['osmid'], attrs['lat'], attrs['lon'], attr['osmid'], attr['user'])

        #    def node(self, lat="", lon="", tags=list(), modified=False, osmid=None, user=None, uid=None, version=None):
    def node(self, tags=list(), attrs=dict(), modified=False):
        #        timestamp = ""  # LastUpdate
        timestamp = time.strftime("%Y-%m-%dT%TZ")
        # self.file.write("       <node id='" + str(self.osmid) + "\' visible='true'")
        if len(attrs) > 0:
            self.file.write("    <node")
            for ref,value in attrs.items():
                self.file.write(" " + ref + "=\"" + value + "\"")
            if len(tags) > 0:
                self.file.write(">\n")
            else:
                self.file.write("/>\n")

        for i in tags:
            for name, value in i.items():
                if name == "Ignore" or value == '':
                    continue
                if str(value)[0] != 'b':
                    if value != 'None' or value != 'Ignore':
                        tag = self.makeTag(name, value)
                        for newname, newvalue in tag.items():
                            self.file.write("     <tag k=\"" + newname + "\" v=\"" + str(newvalue) + "\"/>\n")

        if len(tags) > 0:
            self.file.write("    </node>\n")
        self.osmid = self.osmid - 1

        return self.osmid - 1

    # Here's where the fun starts. Read a field header from a file,
    # which of course are all different. Make an attempt to match these
    # random field names to standard OSM tag names. Same for the values,
    # which for OSM often have defined ranges.
    def makeTag(self, field, value):
        newval = str(value)
        #newval = html.unescape(newval)
        newval = newval.replace('&', 'and')
        newval = newval.replace('"', '')
        #newval = newval.replace('><', '')
        tag = dict()
        # logging.debug("OSM:makeTag(field=%r, value=%r)" % (field, newval))

        try:
            newtag = self.ctable.match(field)
        except Exception as inst:
            logging.debug("MISSING Field: %r" % field)
            # If it's not in the conversion file, assume it maps directly
            # to an official OSM tag.
            newtag = field

        newval = self.ctable.attribute(newtag, newval)
        # logging.debug("ATTRS1: %r %r" % (newtag, newval))
        change = newval.split('=')
        if len(change) > 1:
            newtag = change[0]
            newval = change[1]
            # logging.debug("ATTRS2: %r %r" % (newtag, newval))
        #if newtag == 'name':
            #tag[newtag] = BeautifulSoup(newval, "lxml")
            #tag[newtag] = newval.replace('&#39;', "XXXs")
        #     # logging.debug("CAPITALIZE %r %r" % (newtag, newval))
        else:
            tag[newtag] = newval

        return tag

    def makeWay(self, refs, tags=list(), attrs=dict()):
        if len(refs) is 0:
            logging.debug("ERROR: No refs! %r" % tags)
            return

        if len(attrs) > 0:
            self.file.write("  <way")
            for ref,value in attrs.items():
                self.file.write("    " + ref + "=\"" + value + "\"")
            self.file.write(">\n")
        else:
            # logging.debug("osmfile::way(refs=%r, tags=%r)" % (refs, tags))
            #logging.debug("osmfile::way(tags=%r)" % (tags))
            self.file.write("    <way")
            #timestamp = time.strftime("%Y-%m-%dT%TZ")

            self.file.write(" version='1'")
            self.file.write(" timestamp='" + timestamp + "\'")
            self.file.write(" user='" + self.options.get('user') + "' uid='" +
                            str(self.options.get('uid')) + "'>'\n")

        # Each ref ID points to a node id. The coordinates is im the node.
        for ref in refs:
            # FIXME: Ignore any refs that point to ourself. There shouldn't be
            # any, so this is likely a bug elsewhere when parsing the geom.
            if ref == self.osmid:
                break
            self.file.write("    <nd ref=\"" + str(ref) + "\"/>\n")

        value = ""

        for i in tags:
            for name, value in i.items():
                if name == "Ignore" or value == '':
                    continue
                if str(value)[0] != 'b':
                    self.file.write("    <tag k=\"" + name + "\" v=\"" +
                                    str(value) + "\"/>\n")

        self.file.write("  </way>\n")

    def makeRelation(self, members, tags=list(), attrs=dict()):
        if len(attrs) > 0:
            self.file.write("  <relation")
            for ref,value in attrs.items():
                self.file.write(" " + ref + "=\"" + value + "\"")
            self.file.write(">\n")

        # Each ref ID points to a node id. The coordinates is im the node.
        for mattr in members:
            for ref, value in mattr.items():
                #print("FIXME: %r %r" % (ref, value))
                if ref == 'type':
                    self.file.write("    <member")
                self.file.write(" " + ref + "=\"" + value + "\"")
                if ref == 'role':
                    self.file.write("/>\n")

        value = ""

        for i in tags:
            for name, value in i.items():
                if name == "Ignore" or value == '':
                    continue
                if str(value)[0] != 'b':
                    self.file.write("    <tag k=\"" + name + "\" v=\"" + str(value) + "\"/>\n")
            
        self.file.write("  </relation>\n")
