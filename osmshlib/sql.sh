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

poly_exists ()
{
#    echo "TRACE: $*"
    
    local poly=$"1"
    
    # See if the polygon exists in the database. If not we obviously can't
    # use it.
    local rows=`psql --tuples-only --dbname=${database} --command="SELECT name FROM planet_osm_polygon WHERE name='${poly}'""`
    
    if test x"${rows}" = x; then
	return 1
    fi

    return 0
}

# Setup the query as a string to avoid weird shell escaping syntax ugliness
# $1 - The subset
# $2 - The output file name
# returns the name of the SQL file
#
# All Queries need to have osm_id, name, and the coordinates as the first 3
# fileds returned to make later parsing consistent.
sql_file ()
{
#    echo "TRACE: $*"

    local subset="$1"
    local sqlout="`echo $2 | tr ' ' '-'`.sql"
    rm -f ${sqlout}
    local polysql=""
    
    case "${subset}" in
	# We only want trails that aren't ski trails, as piste routes get different
	# colors. The only way we can tell the difference is if the piste:type tag
	# exists.
	trails)
#		cat <<EOF >> ${sqlout}
#SELECT line.osm_id,line.name,line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access,ST_AsKML(line.way) FROM planet_osm_line AS line, dblink('dbname=polygons', 'select name,geom FROM boundary') AS poly(name name,geom geometry) WHERE poly.name='${polygon}' AND (ST_Crosses(line.way,poly.geom) OR ST_Contains(poly.geom,line.way)) AND (line.highway='footway' OR line.highway = 'path');
#EOF
		# Works!
#		if test "`echo ${polygons[$i]} | grep -c poly`" -eq 0; then
#		    cat <<EOF >> ${sqlout}
#SELECT line.osm_id,line.name,line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access,ST_AsKML(line.way) FROM planet_osm_line AS line, (SELECT name,way FROM planet_osm_polygon WHERE name='${folder}') AS poly WHERE (ST_Crosses(line.way,poly.way) OR ST_Contains(poly.way,line.way)) AND (line.highway='foo-tway' OR line.highway = 'path');
#EOF
#		else
	    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name,ST_AsKML(line.way),line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access FROM planet_osm_line AS line WHERE line.highway='footway' OR line.highway = 'path';
EOF
#		fi
#		cat <<EOF >> ${sqlout}
#SELECT planet_osm_line.osm_id,planet_osm_line.name,planet_osm_line.tags->'sac_scale',planet_osm_line.tags->'bicycle',planet_osm_line.tags->'mtb:scale:imba',planet_osm_line.access,ST_AsKML(planet_osm_line.way) FROM planet_osm_line,planet_osm_polygon WHERE ((planet_osm_line.highway = 'footway' OR planet_osm_line.highway = 'path') AND planet_osm_line.tags?'piste:type' != 't') ${polysql};
#EOF
	    ;;
	piste)
	    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name FROM planet_osm_line AS line, (SELECT name,way FROM planet_osm_polygon WHERE name='Parco Nazionale dello Stelvio') AS poly WHERE (ST_Crosses(line.way,poly.way) OR ST_Contains(poly.way,line.way));
# SELECT line.osm_id,line.name,line.tags->'piste:type',line.tags->'piste:difficulty',line.tags->'piste:grooming',line.aerialway,line.access,ST_AsKML(line.way) FROM planet_osm_line AS line, (SELECT name,way FROM planet_osm_polygon WHERE name='${folder}') AS poly WHERE (ST_Crosses(line.way,poly.way) OR ST_Contains(poly.way,line.way)) AND (line.tags?'piste:type' = 't' OR line.aerialway = 'chair_lift');
EOF
#		cat <<EOF >> ${sqlout}
#SELECT planet_osm_line.osm_id,planet_osm_line.name,planet_osm_line.tags->'piste:type',planet_osm_line.tags->'piste:difficulty',planet_osm_line.tags->'piste:grooming',planet_osm_line.aerialway,planet_osm_line.access,ST_AsKML(planet_osm_line.way) from planet_osm_line,planet_osm_polygon WHERE (planet_osm_line.tags?'piste:type' = 't' OR planet_osm_line.erialway = 'chair_lift') ${polysql};
#EOF
	    ;;
	fire)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(line.way),tags->'emergency',amenity,highway,tourism,tags->'fire_hydrant:type' from planet_osm_point;
EOF
	    ;;
	wifi)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way) from planet_osm_point WHERE tags->'internet_access'='wlan';
EOF
	    ;;
	waterfall)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tags->'name.en',tags->'description' from planet_osm_point WHERE waterway='waterfall';
EOF
	    ;;
	swimming)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),name.en,description from planet_osm_point WHERE tags->'sport'='swimming' AND tags->'amenity'!='swimming_pool' ${polysql};
EOF
	    ;;
	lodging)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber' from planet_osm_point WHERE tourism='guest_house' OR tourism='hotel' OR tourism='hostel' ${polysql};
EOF
	    ;;
	roads)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),highway from planet_osm_line WHERE highway='secondary' OR highway='tertiary' OR highway='unclassified' OR highway='residential' OR highway='service' OR planet_osm_line.highway='track';
EOF
	    ;;
	*)
	    ;;
    esac

    echo ${sqlout}
    return 0
}
