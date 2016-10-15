#!/bin/bash

# 
#   Copyright (C) 2016
#   Free Software Foundation, Inc.
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

infile="$1"
name="${tmpdir}/`echo "${infile}" | sed -e 's:\-poly\.kml:.poly:'`"
name="`basename "${name}" | sed -e 's:\.poly::' #> ${outfile}`"
outfile="${name}.poly"

declare -a ways=(`egrep -n "<coordinates|</coordinates>" "${infile}" | cut -d ':' -f 1`)
top=${ways[$a]}
a=`expr $a + 1`
bot=${ways[$a]}
#if test x"${top}" = x -o x"${bot}" = x; then
#fi

padding="     "

echo "${name}" | sed -e 's:\.poly::'
echo "1"

coords="`sed -n ${top},${bot}p "${infile}" | grep -v "coordinate"`"
for i in ${coords}; do
    lat="`echo $i | cut -d ',' -f 1`"
    lon="`echo $i | cut -d ',' -f 2`"
    echo "${padding}${lat}${padding}${lon}"
done

echo "END"
echo "END"


