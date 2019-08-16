
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

import sys
import os.path
import time
import logging
from datafile import convfile
import config
import html
import string
import epdb
from subprocess import PIPE, Popen, STDOUT
import subprocess
ON_POSIX = 'posix' in sys.builtin_module_names
from datetime import datetime
import correct
import overpass
from poly import Poly


class osmfile(object):
    """OSM File output"""
    def __init__(self, options, filespec=None):
        self.options = options
        # Read the config file to get our OSM credentials, if we have any
        # self.config = config.config(self.options)
        self.version = 3
        self.visible = 'true'
        self.osmid = -30470
        # Open the OSM output file
        if filespec is None:
            self.file = self.options.get('outdir') + "foobar.osm"
        else:
            self.file = open(filespec + ".osm", 'w')
        logging.info("Opened output file: " + filespec )
        #logging.error("Couldn't open %s for writing!" % filespec)

        # This is the file that contains all the filtering data
        self.ctable = convfile(options.get('convfile'))

    def isclosed(self):
        return self.file.closed

    def header(self):
        if self.file is not False:
            self.file.write('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n')
            #self.file.write('<osm version="0.6" generator="gosm 0.1" timestamp="2017-03-13T21:43:02Z">\n')
            self.file.write('<osm version="0.6" generator="gosm 0.1">\n')

    def footer(self):
        #logging.debug("FIXME: %r" % self.file)
        self.file.write("</osm>\n")
        if self.file != False:
            self.file.close()

    def makeNode(self, attr=dict()):
        self.node(attr['osmid'], attrs['lat'], attrs['lon'], attr['osmid'], attr['user'])

        #    def node(self, lat="", lon="", tags=list(), modified=False, osmid=None, user=None, uid=None, version=None):
    def node(self, tags=list(), attrs=dict(), modified=False):
        #        timestamp = ""  # LastUpdate
        timestamp = time.strftime("%Y-%m-%dT%TZ")
        # self.file.write("       <node id='" + str(self.osmid) + "\' visible='true'")
        try:
            x = attrs['osmid']
        except:
            try:
                x = attrs['id']
            except:
                attrs['id'] = str(self.osmid)
                self.osmid -= 1

        try:
            x = str(attrs['user'])
        except:
            attrs['user'] = str(self.options.get('user'))
        try:
            x = str(attrs['uid'])
        except:
            attrs['uid'] = str(self.options.get('uid'))

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
                            # if newname == 'addr:street' or newname == 'addr:full' or newname == 'name' or newname == 'alt_name':
                            #     newvalue = string.capwords(newvalue)

                            self.file.write("    <tag k=\"" + newname + "\" v=\"" + str(newvalue) + "\"/>\n")

        if len(tags) > 0:
            self.file.write("    </node>\n")

        return self.osmid

    # Here's where the fun starts. Read a field header from a file,
    # which of course are all different. Make an attempt to match these
    # random field names to standard OSM tag names. Same for the values,
    # which for OSM often have defined ranges.
    def makeTag(self, field, value):
        fix = correct.correct()
        newval = str(value)
        #newval = html.unescape(newval)
        newval = newval.replace('&', 'and')
        newval = newval.replace('"', '')
        #newval = newval.replace('><', '')
        tag = dict()
        #print("OSM:makeTag(field=%r, value=%r)" % (field, newval))

        try:
            newtag = self.ctable.match(field)
        except Exception as inst:
            #logging.warning("MISSING Field: %r, %r" % (field, newval))
            # If it's not in the conversion file, assume it maps directly
            # to an official OSM tag.
            newtag = field

        newval = self.ctable.attribute(newtag, newval)
        #logging.debug("ATTRS1: %r %r" % (newtag, newval))
        change = newval.split('=')
        if len(change) > 1:
            newtag = change[0]
            newval = change[1]

        # name tags, usually roads or addresses, often have to be tweaked
        # for OSM standards
        if (newtag == "name") or (newtag == "alt_name"):
            newval = string.capwords(fix.alphaNumeric(newval))
            newval = fix.abbreviation(newval)
            newval = fix.compass(newval)
        tag[newtag] = newval
        # tag[newtag] = string.capwords(newval)

        #print("ATTRS2: %r %r" % (newtag, newval))
        return tag

    def makeWay(self, refs, tags=list(), attrs=dict()):
        if len(refs) is 0:
            logging.error("No refs! %r" % tags)
            return

        if len(attrs) > 0:
            self.file.write("  <way")
            for ref,value in attrs.items():
                self.file.write("    " + ref + "=\"" + value + "\"")
            self.file.write(">\n")
        else:
            #try:
            #    x = attrs['osmid']
            #except:
            #    attrs['id'] = str(self.osmid)

            #logging.debug("osmfile::way(refs=%r, tags=%r)" % (refs, tags))
            #logging.debug("osmfile::way(tags=%r)" % (tags))
            self.file.write("    <way")
            timestamp = time.strftime("%Y-%m-%dT%TZ")

            self.file.write(" version='1'")
            self.file.write(" id=\'" + str(self.osmid) + "\'")
            self.file.write(" timestamp='" + timestamp + "\'>\n")
#            self.file.write(" user='" + self.options.get('user') + "' uid='" +
#                            str(self.options.get('uid')) + "'>'\n")

        # Each ref ID points to a node id. The coordinates is im the node.
        for ref in refs:
            # FIXME: Ignore any refs that point to ourself. There shouldn't be
            # any, so this is likely a bug elsewhere when parsing the geom.
            # logging.debug("osmfile::way(ref=%r, osmid=%r)" % (ref, self.osmid))
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
        self.osmid = int(self.osmid) - 1

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

    def cleanup(self, tags):
        cache = dict()
        for tag in tags:
            for name, value in tag.items():
                try:
                    if cache[name] != value:
                        tmp = cache[name]
                        cache[name] += ';' + value
                except:
                    cache[name] = value

        tags = list()
        tags.append(cache)
        return tags


class osmConvert(object):
    def __init__(self, file=None):
        """This class uses osmconvert to apply a changeset to an OSM file"""
        self.file = file
        # Make changeset file
        # osmconvert interpreter --out-o5m -o=interpreter.o5m
        # osmconvert previous.osm interpreter.o5m -o now.osm

    def getLastTimestamp(self, file=None):
        """First find the last timestamp in the OSM file so we know where
        to start the adiff."""

        if file is None and self.file is not None:
            file = self.file

        if os.path.exists(file) is False:
            logging.warning("%s does not exist!" % file)
            return None
        else:
            if os.stat(file).st_size == 0:
                logging.error("%s has zero content!" % file)
                return None

        cmd = "grep -o 'timestamp=.[0-9A-Z:-]*'" + " " + file + " | sort -M | tail -1"
        grep = subprocess.check_output(cmd, shell=True)
        if len(grep) == 0:
            logging.error("Couldn't get last timestamp from %s!" % file)
            return None
        # Clean up the timestamp and make it a datetime type
        timestamp = grep.decode('utf-8').split('=')[1].strip('\n\"Z')
        return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')

    def createChanges(self, adiff=None):
        """This method takes an adiff file as produced by the Overpass QL
        server, which then later gets applied to produce an updated OSM file."""
        if adiff is None and self.file is not None:
            adiff = self.file

        if os.path.exists(adiff) is False:
            logging.error("%s doesn't exist!" % adiff)
            return None

        outfile = "/tmp/osmc" + str(os.getpid()) + '.o5m'
        cmd = "osmconvert " + adiff + " --out-o5m -o=" + outfile
        diff = subprocess.check_output(cmd, shell=True)
        if len(diff) == 0:
            return outfile

    def applyChanges(self, file=None):
        """Apply the chngeset file to the osm file"""
        if file is None and self.file is not None:
            file = self.file

        if os.path.exists(file) is False:
            logging.error("%s doesn't exist!" % file)
            return False

        os.rename(file, "tmp.osm")
        adiff = "/tmp/osmc" + str(os.getpid()) + '.o5m'
        cmd = 'osmconvert ' + "tmp.osm " + adiff + ' -o=' + file
        osmc = subprocess.check_output(cmd, shell=True)

        return True

    def applyPoly(self, poly, infile, outfile):
        """This method use an OSM poly file to produce a subset
        from a larger dataset
        """
        if os.path.exists(poly) is False:
            logging.error("%s doesn't exist!" % adiff)
            return None

        cmd = ["osmconvert", "-B=" + poly, "-o=" + outfile, "--max-refs=400000", "--drop-broken-refs", "--complete-ways", infile]
        ppp = Popen(cmd, stdout=PIPE, bufsize=0, close_fds=ON_POSIX)
        ppp.wait()

        logging.info("Produced %s from %s using %s" % (outfile, infile, poly))


# script for Overpass that works. Get everthing.
# (
#   way(39.75,-105.71,40.12,-105.31);
#   node(39.75,-105.71,40.12,-105.31);
#   rel(39.75,-105.71,40.12,-105.31);
#   <;
#   >;
# );
# out meta;
class OverpassXAPI(object):
    """Get data from OSM using the Overpass API"""
    def __init__(self, bbox, filespec=None):
        api = overpass.API()
        query = overpass.MapQuery(bbox[2], bbox[0], bbox[3], bbox[1])
        response = api.get(query, responseformat="xml")

        if filespec is None:
            outfile = open('foo.osm', 'w')
        else:
            outfile = open(filespec, 'w')

        outfile.write(response)
        outfile.close()
