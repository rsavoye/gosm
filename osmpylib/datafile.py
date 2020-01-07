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

import logging
# import epdb
# import re


class convfile(object):
    """Data file for the conversion"""
    def __init__(self, file=""):
        self.table = dict()
        self.attrtable = dict()
        if file != '':
            self.file = self.open(file)
        self.filespec = file

    def open(self, file):
        if file is False:
            return
        try:
            self.file = open(file, "r")
            logging.info("Opened %r" % file)
        except Exception as inst:
            logging.error("Couldn't open %r: %r" % (file), inst)
        self.read()

    def read(self):
        if self.file is False:
            self.file.open(self.filespec)
        if self.file is False:
            return
        lines = self.file.readlines()
        curname = ""
        for line in lines:
            if line[0] == '#':
                continue
            # Drop any embedded commas
            line.replace(", ", " ")
            tmp = line.split(',')
            # First field of the CSV file is the name
            type = tmp[0]
            try:
                name = tmp[1]
            except Exception as inst:
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
            except Exception as inst:
                value = ""

            if type == 'attribute':
                try:
                    attr = tmp[3].replace("\n", "")
                except Exception as inst:
                    attr = ""

                # logging.debug("datafile:read(name=%r, value=%r, attr=%r) is attribute" % (name, value, attr))
                items[value] = str(attr)
                self.attrtable[name] = items
            elif type == 'tag':
                # logging.debug("datafile:read(name=%r, value=%r) is tag" % (name, value.replace("\n", "")))
                self.table[name] = value.replace("\n", "")
            elif type == 'column':
                # logging.debug("datafile:read(name=%r, value=%r) i column" % (name, value.replace("\n", "")))
                self.table[name] = value.replace("\n", "")
            # print("ATTRTABLE: %r" % self.attrtable)

    def attribute(self, name, attr):
        # logging.debug("datafile:attribute(%r) = %r" % (name, attr))
        # m = re.search(pattern, match)
        # Drop any embedded commas
        try:
            value = self.attrtable[name][attr.replace(", ", " ")]
            # logging.debug("Yes VAL: %r" % value)
            return value
        except KeyError:
            # logging.debug("No VAL for: %r" % name)
            return attr

    def match(self, instr):
        # logging.debug("datafile:match(%r) %r" % (name, instr))
        try:
            field = self.table[instr]
        except Exception as inst:
            field = instr
        return field
    
    def dump(self):
        logging.info("Dumping datafile")
        for i, j in self.table.items():
            logging.info("FOOBAR: %r" % (i, j))


