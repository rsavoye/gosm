#!/usr/bin/python3
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
import logging
import pdb

class dejagnu(object):
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.xfail = 0
        self.xpass = 0
        self.untested = 0
        self.unresolved = 0

    def fails(self, msg=""):
        self.failed += 1
        print("FAIL: " + msg)

    def untested(self, msg=""):
        self.untested += 1
        print("UNTESTED: " + msg)

    def passes(self, msg=""):
        self.failed += 1
        print("FAIL: " + msg)

    def matches(self, instr, expected, msg=""):
        pdb.set_trace()
        if instr is expected:
            self.passes(msg)
            return True
        else:
            self.fails(msg)
            return False
        
    def totals(self):
        if self.passed > 0:
            print("Total passed: %r " % self.passed)
        if self.failed > 0:
            print("Total failed: %r " % self.failed)
        if self.untested > 0:
            print("Total untested: %r " % self.untested)
        if self.unresolved > 0:
            print("Total unresolved: %r " % self.unresolved)
