#!/bin/bash - 
#===============================================================================
#
#          FILE: osmid2kml.sh
# 
#   DESCRIPTION: 
# 
#        AUTHOR: Rob Savoye (), rob@senecass.com
#  ORGANIZATION: Seneca Software & Solar, Inc
#       CREATED: 02/26/2017 11:02:37 AM
#      REVISION:  ---
#===============================================================================
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

set -o nounset                              # Treat unset variables as an error

usage()
{
    cat <<EOF
    $0 [options]
EOF
    exit
}

if test $# -lt 1; then
    usage
fi

osmids="`echo $1 | tr ',' ' '`"
declare -a select=()
database="cuba"
outfile="${database}.kml"
title="${database}"

rm -f ${outfile}
cat <<EOF > ${outfile}
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2">
<Document>
    <name>${title}</name>
    <description></description>
    <visibility>1</visibility>
    <open>1</open>
EOF

cat `dirname $0`/styles.xml >> ${outfile}

i=0
for id in ${osmids}; do
    select[$i]="${id}"
    i="`expr $i + 1`"
done

# Excute the SQL query
name=""
coords=""
tables="planet_osm_line planet_osm_polygon planet_osm_point"
	  
i=0
while test $i -lt ${#select[@]}; do
    for table in ${tables}; do
	out=`psql --tuples-only --dbname=${database} --command="SELECT name,ST_AsKML(way) FROM ${table} WHERE osm_id='${select[$i]}';"`
	name="`echo ${out} | tr -s '' | cut -d '|' -f 1 | sed -e 's:&:and:'`"
	coords="`echo ${out} | cut -d '|' -f 2`"
#	if test x"${coords}" = x -o x"${name}" = x; then
	if test x"${coords}" = x; then
	    continue
	fi
	echo "Processing ${name}..."
	cat <<EOF >> ${outfile}
        <Placemark>
              <name>${name:-Unknown $i}</name>
	      <styleUrl>#Wifi</styleUrl>
EOF
	echo ${coords} | egrep "<Point>.*</Point>|<Polygon>.*</Polygon>" >> ${outfile}
	cat <<EOF >> ${outfile}
        </Placemark>
EOF
    done
    i="`expr $i + 1`"
done
cat <<EOF >> ${outfile}
</Document>
</kml>
EOF

echo "KML file is: ${outfile}"
