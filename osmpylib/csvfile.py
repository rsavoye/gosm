# 
# Copyright (C) 2017, 201, 2019, 2020   Free Software Foundation, Inc.
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


class csvfile(object):
    def __init__(self, file=""):
        if file != "":
            self.open(file)

    def open(self, file):
        if os.path.isfile(file):
            self.file = open(file, 'w')
        else:
            self.file = open(file, 'x')
        logging.info("Opened output file: " + file)

    def header(self, fields):
        start = True
        for field in fields:
            if start == True:
                start = False
                self.file.write(field)
            else:
                self.file.write("," + field)

    def entry(self, data):
        start = False
        for column in data:
            if start == True:
                start = False
                self.file.write(column)
            else:
                self.file.write("," + column)
                
