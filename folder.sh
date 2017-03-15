#!/bin/bash

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

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have tags signifying what type
# it is.

# load commonly used functions
osmbin="`which $0`"
topdir="`dirname ${osmbin}`"
. "${topdir}/osmshlib/colors.sh" || exit 1
. "${topdir}/osmshlib/parse.sh" || exit 1
. "${topdir}/osmshlib/sql.sh" || exit 1
. "${topdir}/osmshlib/kml.sh" || exit 1

usage()
{
    local sup="`echo ${supported} | sed -e 's/ /[:name],/g'`"
    
    cat <<EOF
    $0 [options]
	--infile(-i)  input file
EOF
    exit
}

if test $# -lt 1; then
    usage
fi

infile=""

OPTS="`getopt -o h:i: -l infile:,help`"
while test $# -gt 0; do
    case $1 in
        -i|--infile) infile=$2 ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

declare -a fs=(`grep -n '<Folder>' ${infile} | cut -d ':' -f 1`)
declare -a fe=(`grep -n '</Folder>' ${infile} | cut -d ':' -f 1`)

for i in ${!fs[@]}; do
    j=`expr ${fs[$i]} + 1`
    name=`sed -e "$j,$j!d" ${infile} -e 's:.*<name>::'  -e 's:</name>::'`
done

for i in ${!fs[@]}; do
    j=`expr ${fs[$i]} + 1`
    name=`sed -e "$j,$j!d" ${infile} -e 's:.*<name>::'  -e 's:</name>::'`
    outfile="`echo ${name}.kml | tr -d ' '`"
    kml_file_header "${outfile}" "${name}"
    sed -e "${fs[$i]},${fe[$i]}!d" ${infile} >> "${outfile}"
    kml_file_footer ${outfile}
done

