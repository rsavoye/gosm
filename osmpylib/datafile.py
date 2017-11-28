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

import logging
import os


class convfile(object):
    """Data file for the conversion"""
    def __init__(self, file=""):
        self.table = dict()
        self.attrtable = dict()
        if file != '':
            self.file = self.open(file)
        self.filespec = file

    def open(self, file):
        try:
            self.file = open(file, "r")
        except:
            logging.error("Couldn't open " + file)
        self.read()

    def read(self):
        #import pdb; pdb.set_trace()
        if self.file == False:
            self.file.open(self.filespec)
        try:
            lines = self.file.readlines()
        except:
            logging.error("Couldn't read lines from %r" % self.file)
            return
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
        #logging.debug("datafile:attribute(%r) %r" % (name, attr))
        try:
            value = self.attrtable[name][attr]
            #print("Yes VAL: %r" % value)
            return value
        except KeyError:
            #print("No VAL for: %r" % name)
            return attr

    def match(self, instr):
        #logging.debug("datafile:match(%r) %r" % (name, instr))
        try:
            field = self.table[instr]
        except:
            field = instr
        return field
    
    def dump(self):
        logging.info("Dumping datafile")
        for i,j in self.table.items():
            logging.info("FOOBAR: %r" % (i, j))
            

