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
    echo "$0 infile polyfile1,polyfile2,polyfile3,..."

    cat <<EOF
--infile(-i) FILE      - Input file in osm, pbf, or zip (ERSI)
--polyfile(-p) FILE(s) - Polyfile(s) to produce data subsets
--help(-h)             - Display usage

This program is a simple utility to setup a database properly for importing
data from wither and OSM file or a Shapefile (ERSI).
EOF
    exit
}

if test $# -lt 1; then
    usage
fi

infile="$1"
polys="$2"

OPTS="`getopt -o p:h -l polyfile:,help`"
while test $# -gt 0; do
    case $1 in
        -i|--infile) infile=$2 ;;
        -p|--polyfile) polys=$2 ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

declare -a polyfiles=()
i=0
for db in `echo ${polys} | tr ',' ' '`; do
    polyfiles[$i]="${db}"
    i="`expr $i + 1`"
done

# Look at the suffix to determine the input file type, as the 'file'
# command just thinks it's an XML file. (which it is)
filetype="`echo ${infile} | sed -e 's:^.*\.::'`"
if test x"${filetype}" = x"osm"; then
    filetype="xml"
fi

i=0
while test $i -lt ${#polyfiles[@]}; do
    dbname="`basename ${polyfiles[$i]} | sed -e 's:\.poly::'`"

    exists="`psql -l | grep -c ${dbname}`"
    # Note that the user running this script must have the right permissions.
    if test "${exists}" -eq 0; then
	createdb -EUTF8 ${dbname} -T template0
	if test $? -gt 0; then
	    echo "ERROR: createdb ${dbname} failed!"
	    exit
	fi
	psql ${dbname} -c 'create extension hstore;'
	if test $? -gt 0; then
	    echo "ERROR: couldn't add hstore extension!"
	    exit
	fi
	psql ${dbname} -c 'create extension postgis;'
	if test $? -gt 0; then	
	    echo "ERROR: couldn't add postgis extension!"
	    exit
	fi
	psql ${dbname} -c 'create extension dblink;'
	if test $? -gt 0; then	
	    echo "ERROR: couldn't add dblink extension!"
	    exit
	fi
    fi
    
    case ${filetype} in
	xml|pbf|osm)
	    osmosis --read-${filetype} file="${infile}" --bounding-polygon file=${polyfiles[$i]} --write-xml file=${dbname}.osm
	    if test $? -gt 0; then
		exit
	    fi
	    osm2pgsql -v --slim -C 1500 -d ${dbname} --number-processes 8 ${dbname}.osm --hstore
	    if test $? -gt 0; then
		exit
	    fi
	    # rm -f ${dbname}.osm
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
    i="`expr $i + 1`"
done
