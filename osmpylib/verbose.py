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

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have tags signifying what type
# it is.

import os
import pdb
import sys


class verbose(object):
    """Debugging support for this program."""
    def __init__(self, value):
        self.verbosity = value
        self.tracef = False

    def toggle(self):
        if self.verbosity is False:
            self.verbosity = True
        else:
            self.verbosity = False

    def log(self, msg):
        if self.verbosity is True:
            str = msg
            print(str)

    def trace(self):
        import inspect
        frame = inspect.currentframe()
        #print("FOO: " + inspect.getargsvalue(frame))
        print("TRACE: " + (inspect.getouterframes(inspect.currentframe())[1].function) + '()')

    def error(self, msg):
        print("ERROR: " + msg)
        
    def warning(self, msg):
        print("WARNING: " + msg)
        
    def pdb(self):
        # import code
        # code.interact(local=locals())
        import pdb; pdb.set_trace()

    def value(self):
        return self.verbosity

class version(object):
    """Check the version of python."""
    def __init__(self):
        fields = list(sys.version)
        if fields[0] == "3":
            self.version = 3
            print("Python 3")
        else:
            self.version = 2
            print("Python 2")
            
    def version(self):
        return self.version
