#!/bin/bash

# 
#   Copyright (C) 2016, 2017, 2018, 2019   Free Software Foundation, Inc.
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
--database(-d)         - Database to use
--user(-u)	       - Database user name
--passwd(-p)	       - Database password
--recreate(-r)         - Recreate database if it exists
This program is a simple utility to setup a database properly for importing
data from wither and OSM file or a Shapefile (ERSI).
EOF
    exit
}

if test $# -lt 1; then
    usage
fi

infile="$1"
polys=""
dbname=""
dropdb="no"

if test -e ~/.gosmrc; then
    . ~/.gosmrc
fi

OPTS="`getopt -o b:d:hu:p:r -l polyfile:database:,help,dbuser:,dbpasswd:,recreate`"
while test $# -gt 0; do
    case $1 in
        -i|--infile) infile=$2 ;;
        -p|--polyfile) polys=$2 ;;
        -d|--database) dbname=$2 ;;
	-u|--dbuser) dbuser=$2;;
	-b|--passwd) dbpass=$2 ;;
	-r|--recreate) dropdb="yes" ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

if test x"${polys}" = x -a x"${dbname}" = x; then
    echo "ERROR: If no poly file, a database name must be specifed!"
    exit
fi

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
while test $i -lt ${#polyfiles[@]} -o x"${polys}" = x; do
    dbname="${dbname:-`basename ${polyfiles[$i]} | sed -e 's:\.poly::'`}"
    dbname="`basename ${dbname}`"
    echo "Processing ${infile} into ${dbname}..."
    #exists="`psql -l | grep -c ${dbname}`"
    exists=0
    # Note that the user running this script must have the right permissions.
    if test "${exists}" -eq 0; then
	echo "Creating postgresql database ${dbname}"
	if test x"${dropdb}" = x"yes"; then
	    dropdb --if-exists ${dbname} >& /dev/null
	fi
	createdb -EUTF8 ${dbname} ${dbname} -T template0  >& /dev/null
	if test $? -gt 0; then
	    echo "WARNING: createdb ${dbname} failed!"
	    exit
	fi
	psql -d ${dbname} -c 'create extension hstore;' >& /dev/null
	if test $? -gt 0; then
	    echo "ERROR: couldn't add hstore extension!"
	    exit
	fi
	psql -d ${dbname} -c 'create extension postgis;' >& /dev/null
	if test $? -gt 0; then	
	    echo "ERROR: couldn't add postgis extension!"
	    exit
	fi
	psql -d ${dbname} -c 'create extension dblink;' >& /dev/null
	if test $? -gt 0; then	
	    echo "ERROR: couldn't add dblink extension!"
	    exit
	fi
    else
	echo "Postgresql database ${dbname} already exists, not creating."
    fi
    
    if test x"${polys}" = x; then
	polys="done"
    fi

    case ${filetype} in
	xml|pbf|osm)
#	    if test x"${polys}" != x"done" -a ${#polyfiles[@]} -gt 0; then
	    # Only import a region from the input file
	    if test ${#polyfiles[@]} -gt 0; then
		osmosis --read-${filetype} file="${infile}" --bounding-polygon file=${polyfiles[$i]} --write-xml file=${dbname}.osm
		if test $? -gt 0; then
		    exit
		fi
	    fi
	    osm2pgsql -c --slim -C 500 -d ${dbname} --number-processes 8 ${infile} --hstore --input-reader xml --drop >& /dev/null
	    #if test $? -gt 0 -a $? < 127; then
		#	exit
		#echo "FIXME: $?"
	    #fi
	    # ogr2ogr imports relations, sort-of, and osm2pgsql doesn't. We use the
	    # relations or boundaries to create groups, ie.. KML "<Folder>"
	    ogr2ogr -overwrite -f  "PostgreSQL" PG:"dbname=${dbname}" -nlt GEOMETRYCOLLECTION ${infile}
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
