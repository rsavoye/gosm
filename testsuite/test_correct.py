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
import html
import string
import pdb
import re
import correct
import inspect 
import dejagnu

dj = dejagnu.dejagnu()

obj = correct.correct()
dj.verbose_level(2)

# Test the compass corrections. ie... N RoadName' becomes 'North RoadName'
instr = "N 126"
x = obj.compass(instr)
dj.matches(x, 'North 126', "correct.compass(North)")

instr = "S 126"
x = obj.compass(instr)
dj.matches(x, 'South 126', "correct.compass(South)")

instr = "E 126"
x = obj.compass(instr)
dj.matches(x, 'East 126', "correct.compass(East)")

instr = "W 126"
x = obj.compass(instr)
dj.matches(x, 'West 126', "correct.compass(West)")

# Test expanding road name abbreviations
instr = "unnamed Dr"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Drive", "correct.abbreviation(Drive)")

instr = "unnamed Ct"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Court", "correct.abbreviation(Court)")

instr = "unnamed Ave"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Avenue", "correct.abbreviation(Avenue)")

instr = "unnamed rd"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Road", "correct.abbreviation(Road)")

instr = "unnamed ln"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Lane", "correct.abbreviation(Lane)")

instr = "unnamed pl"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Place", "correct.abbreviation(Place)")

instr = "unnamed Trl"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Trail", "correct.abbreviation(Trail)")

instr = "unnamed Cir"
x = obj.abbreviation(instr)
dj.matches(x, "unnamed Circle", "correct.abbreviation(Circle)")

#pdb.set_trace()
instr = "CR unnamed"
x = obj.abbreviation(instr)
dj.matches(x, "County Road unnamed", "correct.abbreviation(CR)")

#pdb.set_trace()
instr = "Hwy unnamed"
x = obj.abbreviation(instr)
dj.matches(x, "Highway unnamed", "correct.abbreviation(Hwy)")

#
instr = "CR 126N"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126N", "correct.alphaNumeric(N))")

instr = "CR 126n"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126N", "correct.alphaNumeric(n))")

instr = "CR 126S"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126S", "correct.alphaNumeric(S))")

instr = "CR 126s"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126S", "correct.alphaNumeric(s))")

instr = "CR 126W"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126W", "correct.alphaNumeric(W))")

instr = "CR 126w"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126W", "correct.alphaNumeric(w))")

instr = "CR 126E"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126E", "correct.alphaNumeric(E))")

instr = "CR 126e"
x = obj.alphaNumeric(instr)
dj.matches(x, "CR 126E", "correct.alphaNumeric(e))")


# All done
if __name__ == '__main__':
    dj.totals()
    
