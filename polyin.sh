#!/bin/bash

usage()
{
    cat <<EOF
    $0 [options]
	--database(-d) database
        --polygon(-p)  existing polygon
        --operation(-o) operation to perform (del|piste|fire|trail|) optional

    When using --title and --operstion del, you dom't need to specify --polygon
EOF
exit
}

# Minimum number of arguments
if test $# -lt 4; then
    usage
fi

osm="yes"
if test x"${osm}" = x"yes"; then
    table="planet_osm_polygon"
else
    table="boundary"
fi

OPTS="`getopt -o d:h:p:t: -l database:,polygon:operation:title:,help`"
while test $# -gt 0; do
    case $1 in
        -d|--database) database=$2 ;;
        -p|--polygon) poly=$2 ;;
        -o|--operation) op=$2 ;;
        -t|--title) title=$2 ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

database="${database:-polygons}"
op="${op:-none}"
poly="${poly}"
name="`echo ${poly} | sed -s 's:.poly::'`"
name="`basename ${name}`"
title="${title:-${name}}"
name="${name:-${title}}"

exists="`psql --dbname=${database} --command="select name from ${table};" | grep -c "${name}"`"

create_tables()
{
    sql="${poly}.sql"
    cat <<EOF > ${sql}

EOF

    return 0
}

create_sql()
{
#    echo "TRACE: $*"
    
    local sql=
    declare -A fields=()
    fields[name]="${1:-'unknown'}"
    fields[geom]=$2

    # landuse, leisure, sport=ski
    if test ${exists} -eq 0; then
	if test x"${osm}" = x"yes"; then
	    case ${op} in
		ski|piste) sql="INSERT INTO ${table} (name,way,boundary,leisure,osm_id,landuse) VALUES ('${fields[name]}',ST_GeomFromText('LINESTRING(${fields[geom]})',900913), 'administrative', 'sports_centre', 0, 'winter_sports')"
		;;
		*) sql="INSERT INTO ${table} (name,way,boundary,osm_id) VALUES ('${fields[name]}',ST_GeomFromText('LINESTRING(${fields[geom]})',900913), 'administrative', 0)"
		   ;;
	    esac
	else
	    sql="INSERT INTO ${table} (name,geom) VALUES ('${fields[name]}',ST_GeomFromText('LINESTRING(${fields[geom]})'));"
	    #    sql="INSERT INTO ${table} (name,polygon) VALUES ('${fields[name]}',ST_MakePolygon(ST_GeomFromText('LINESTRING(${fields[geom]})')));"
	fi
    else
	if test x"${osm}" = x"yes"; then
	    sql="UPDATE ${table} SET way = ST_GeomFromText('LINESTRING(${fields[geom]})',900913);"
	else
	    sql="UPDATE ${table} SET geom = ST_GeomFromText('LINESTRING(${fields[geom]})',900913);"
	fi
    fi
    
    echo "${sql}" > /tmp/sql.$$
    echo "${sql}"
    
    return 0
}

if test x"${op}" = x"del"; then
    psql --dbname=${database} --command="DELETE FROM ${table} WHERE name='${name}'"
    exit
fi

#
# main loop
#
lat=0
lon=0
location=
while read line; do
    if test x"${line:0:1}" = x"-"; then
	lat="`echo ${line} | tr -s ' ' | cut -d ' ' -f 1`"
	lon="`echo ${line} | tr -s ' ' | cut -d ' ' -f 2`"
	if test x"${location}" = x; then
	    location="$lat $lon"
	else
	    location="${location},$lat $lon"
	fi
    fi
done < ${poly}

# (gid, name, perimeter, area, acres, geom)
sql="`create_sql "${name}" "${location}"`"
#echo $sql

if test ${exists} -eq 0; then
    echo "Inserting ${name}"
else
    echo "Updating ${name}"
fi
out="`psql --dbname=${database} --file=/tmp/sql.$$`"

rm -f /tmp/sql.$$

# select name,ST_AsText(geom) from boundary;
# ND01A_NDFD | LINESTRING(-105.470718 39.999771,-105.467475 39.999769,-105.49719 39.950494,-105.496414 39.95089)
