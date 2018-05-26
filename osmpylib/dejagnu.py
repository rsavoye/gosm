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
        self.xfailed = 0
        self.xpassed = 0
        self.untested = 0
        self.unresolved = 0
        self.verbosity = 0

    def verbose_level(self, level=0):
        self.verbosity = level

    def verbose(self, msg="", level=0):
        if self.verbosity > level:
            print(msg)

    def fails(self, msg=""):
        self.failed += 1
        self.verbose("FAIL: " + msg, 1)

    def xfails(self, msg=""):
        self.xfailed += 1
        self.verbose("XFAIL: " + msg, 1)

    def untested(self, msg=""):
        self.untested += 1
        self.verbose("UNTESTED: " + msg, 1)

    def xpasses(self, msg=""):
        self.xpassed += 1
        self.verbose("XPASS: " + msg, 1)

    def passes(self, msg=""):
        self.passed += 1
        self.verbose("PASS: " + msg, 1)

    def matches(self, instr, expected, msg="", yes=True):
        if instr == expected:
            if yes == True:
                self.passes(msg)
            else:
                self.xpasses(msg)
            return True
        else:
            if yes == True:
                self.fails(msg)
            else:
                self.xfails(msg)
            self.verbose("Got \'" + instr + "\', expected \'" + expected + "\'")
            return False
        
    def totals(self):
        print("\nTotals")
        print("-------")
        if self.passed > 0:
            print("Total passed: %r " % self.passed)
        if self.failed > 0:
            print("Total failed: %r " % self.failed)
        if self.untested > 0:
            print("Total untested: %r " % self.untested)
        if self.unresolved > 0:
            print("Total unresolved: %r " % self.unresolved)
