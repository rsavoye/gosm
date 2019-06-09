# 
#   Copyright (C) 2018   Free Software Foundation, Inc.
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

# This class attempts to fix many common errors in OSM names, primarily
# because it break navigation. This script is a bit ugly and brute force,
# but does the trick for me. It's still hard to filter out all bad data,
# but this gets close.
import logging
import string
import epdb
import re


class correct(object):
    def __init__(self):
        self.orig = ""
        self.value = ""
        self.modified = False
        self.dirshort = ("S", "E", "N", "W")
        self.dirlong = ("South", "East", "North", "West")
        self.abbrevs = ("CR", "Hwy", "Rd", "Ln", "Dr", "Cir", "Ave", "Pl", "Trl", "Ct", "CR", "FR")
        self.fullname = ("County Road", "Highway", "Road", "Lane", "Drive", "Circle", "Avenue", "Place", "Trail", "Court", "County Road", "FS")

    def alphaNumeric(self, value=""):
        self.orig = value
        self.value = value
        m = re.search("[0-9]+[abnesw]+$", value)
        if m is not None:
            number = value[0:len(value)-1]
            suffix = string.capwords(value[len(value)-1])
            self.value = str(number) + suffix
            if self.value != value:
                # print("MODIFIED%r to %r" % (value, self.value))
                self.modified = True
        else:
            # print("NO CHANGE, %r" % self.value)
            self.value = value
        return self.value

    def abbreviation(self, value=""):
        self.orig = value
        self.value = value
        # Fix abbreviations for road type
        i = 0
        while i < len(self.abbrevs):
            pattern = " " + self.abbrevs[i] + "$"
            m = re.search(pattern, value, re.IGNORECASE)
            pattern = "^" + self.abbrevs[i] + " "
            n = re.search(pattern, value, re.IGNORECASE)
            if n is not None:
                m = n
            if m is not None:
                pattern = " " + self.abbrevs[i] + " "
                newvalue = value[0:m.start()]
                rest = ' ' + value[m.start() + len(self.abbrevs[i])+1:len(value)]
                self.value = newvalue + ' ' + self.fullname[i] + rest.rstrip(' ')
                self.modified = True
                break

            pattern = " " + self.abbrevs[i] + " "
            m = re.search(pattern, value, re.IGNORECASE)
            if m is not None:
                newvalue = value[0:m.start()]
                rest = ' ' + value[m.start() + len(self.abbrevs[i])+1:len(value)]
                self.value = newvalue + ' ' + self.fullname[i] + rest
                self.modified = True

            # These seem to be special cases
            pattern = " spur"
            m = re.search(pattern, value)
            if m is not None:
                self.value = string.capwords(self.value)
                self.modified = True

            pattern = " Mtn "
            m = re.search(pattern, value)
            if m is not None:
                self.value = self.value.replace(pattern, " Mountain ")
                self.modified = True

            # Look for a few weird Rd patterns
            pattern = " Rd[\) ]+"
            m = re.search(pattern, value, re.IGNORECASE)
            if m is not None:
                self.value = self.value.replace(" Rd", " Road")
                self.modified = True
                break
            i = i +1

        return self.value.lstrip()
    
    def compass(self, value=""):
        self.orig = value
        i = 0
        # Fix compass direction names
        if value[0] == 'S' or value[0] == 'E' or value[0] == 'N' or value[0] == 'W':
            while i < len(self.dirshort):
                pattern = "^" + self.dirshort[i] + ' '
                m = re.search(pattern, value, re.IGNORECASE)
                if m is not None:
                    newvalue = self.dirlong[i] + ' '
                    newvalue += value[2:]
                    self.value = newvalue
                i = i +1

        return self.value

    def ismodified(self):
        return self.modified

