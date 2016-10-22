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

#
# This assume the user running this script has full priviledges for the database.
#
usage()
{
    echo "$0 name infile polyfile"

    cat <<EOF
This program is a simple utility to setup a database properly for importing
data from wither and OSM file or a Shapefile (ERSI).
EOF
}

dbname=$1
infile=$2
poly=$3

exists="`psql -l | grep -c ${dbname}`"
if test "${exists}" -eq 0; then
    #sudo -u ${dbuser} psql template1 -c 'create extension hstore;'
    createdb -EUTF8 ${dbname} -T template0
    psql ${dbname} -c 'create extension hstore;'
    psql ${dbname} -c 'create extension postgis;'
#    sudo -u ${dbuser} createdb -EUTF8 ${name} -T template0
#    sudo -u ${dbuser} psql ${dbname} -c 'create extension hstore;'
#    sudo -u ${dbuser} psql ${dbname} -c 'create extension postgis;'
fi

filetype="`echo ${infile} | sed -e 's:^.*\.::'`"
name="`echo ${infile} | sed -e 's:\..*::'`"

case ${filetype} in
    xml|pbf|osm)
	osmosis --read-${filetype} file="${infile}" --bounding-polygon file="${poly}"  --write-xml file=${dbname}.osm
	if test $? -gt 0; then
	    exit
	fi
	osm2pgsql -v --slim -C 1500 -d ${dbname} --number-processes 8 ${dbname}.osm --hstore
	if test $? -gt 0; then
	    exit
	fi
	;;
    zip)
	unzip -o ${infile}
	rm -f ${name}.sql
	# Sometimes the filenames in the zip don't match the zip filename itsef,
	# so we check for the actual name in the file.
	newname="`unzip -l ${infile} | grep "\.shp$" | tr -s ' ' | cut -d ' ' -f 5 | sed -e 's/.shp//'`"
	shp2pgsql -p ${newname} > ${name}.sql
	if test -e ${name}.sql; then
	    psql ${dbname} < ${name}.sql
	else
	    echo "ERROR: couldn't produce SQL file!"
	fi
	rm -f ${name}.{dbf,prj,shp,shx,sql}
	;;
    *)
	echo "${filetype} not implemented!"
	;;
    #sudo -u ${dbuser} psql -c "GRANT CONNECT on DATABASE ${name} to rob"
esac
