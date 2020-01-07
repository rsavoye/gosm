#!/bin/bash

# 
# Copyright (C) 2016, 2017, 2018, 2019, 2020
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

usage()
{
    echo "$0 infile"

    cat <<EOF
This program is a simple utility to convert a KML file to a poly file, which
can be used to constrain the data set.
EOF
    exit
}

if test $# -lt 1; then
    usage
fi

infile="$1"
name="${tmpdir}/`echo "${infile}" | sed -e 's:\-poly\.kml:.poly:'`"
name="`basename "${name}" | sed -e 's:\.poly::' #> ${outfile}`"
tmpdir="/tmp"
outfile="${tmpdir}/${name}.poly"

declare -a ways=(`egrep -n "<coordinates|</coordinates>" "${infile}" | cut -d ':' -f 1`)
top=${ways[$a]}
a=`expr $a + 1`
bot=${ways[$a]}
#if test x"${top}" = x -o x"${bot}" = x; then
#fi

padding="     "

touch ${outfile}

echo "${name}" | sed -e 's:\.poly::' >> ${outfile}
echo "1" >> ${outfile}


coords="`sed -n ${top},${bot}p "${infile}" | grep -v "coordinate"`"
for i in ${coords}; do
    lat="`echo $i | cut -d ',' -f 1`"
    lon="`echo $i | cut -d ',' -f 2`"
    echo "${padding}${lat}${padding}${lon}" >> ${outfile}
done

echo "END" >> ${outfile}
echo "END" >> ${outfile}

echo "Polyfile is: ${outfile}"
