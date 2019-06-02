# 
#   Copyright (C) 2017,2018,2019   Free Software Foundation, Inc.
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

# See if the polygon exists in the database. If not we obviously can't
# use it.
poly_exists ()
{
#    echo "TRACE: $*"
    
    local poly=$"1"
    
    local rows=`psql --tuples-only --dbname=${database} --command="SELECT name FROM planet_osm_polygon WHERE name='${poly}'""`
    
    if test x"${rows}" = x; then
	return 1
    fi

    return 0
}

# a few functions to see if data of the requested type exists in the database
count_roads ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_line WHERE highway is not NULL AND highway!='path' OR highway!='footway' OR highway!='cycleway'" | tr -d ' '`"

    #echo "Found ${result} roads"
    echo "${result}"
    return ${result}
}

count_trails ()
{
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_line WHERE highway='path' OR highway='footway' OR highway='cycleway'" | tr -d ' '`"
    
    #echo "Found ${result} trails"
    echo "${result}"
    return ${result}
}

count_huts ()
{
    local result="$(psql --tuples-only --dbname=${database} --command="SELECT osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber' from planet_osm_point WHERE tourism='wilderness_hut' OR tourism='alpine_hut' ${polysql};")"

    if test x"${result}" = x; then
	result=0
    fi
    echo ${result}
    return ${result}
}

count_lodging ()
{
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE tourism='hotel' OR tourism='hostel' OR tourism='guest_house'" | tr -d ' '`"

    #echo "Found ${result} trails"
    echo ${result}
    return ${result}
}

count_peaks ()
{
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE natural='peak'" | tr -d ' '`"

    #echo "Found ${result} trails"
    echo ${result}
    return ${result}
}

count_places ()
{
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE place='hamlet' OR place='village' OR place='town' OR place='isolated_dwelling' OR place='locality'" | tr -d ' '`"

    #echo "Found ${result} trails"
    echo ${result}
    return ${result}
}

count_swimming ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE tags->'sport'='swimming' AND tags->'amenity'!='swimming_pool'" | tr -d ' '`"

    #echo "Found ${result} swimming locations"
    echo ${result}
    return ${result}
}

count_historic ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE historic is not NULL" | tr -d ' '`"

    #echo "Found ${result} historic sites"
    echo ${result}
    return ${result}
}

count_camp ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE tourism='camp_site' OR  amenity='campground'"  | tr -d ' '`"

    #echo "Found ${result} camp sites"
    echo ${result}
    return ${result}
}

count_firewater ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT COUNT(*) FROM planet_osm_point WHERE tags->'emergency'='fire_hydrant' OR tags->'emergency'='water_tank'" | tr -d ' '`"

    #echo "Found ${result} emergency water sources"
    echo ${result}
    return ${result}
}

count_helicopter ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT COUNT(*) FROM planet_osm_point WHERE tags->'aeroway'='helipad' OR tags->'emergency'='landing_site'" | tr -d ' '`"

    #echo "Found ${result} landing sites"
    echo ${result}
    return ${result}
}

count_stations ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT COUNT(*) FROM planet_osm_point WHERE tags->'emergency'='fire_station'" | tr -d ' '`"

    #echo "Found ${result} emergency fire stations"
    echo ${result}
    return ${result}
}

count_piste ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_line WHERE tags->'piste:type' is not NULL" | tr -d ' '`"

    #echo "Found ${result} emergency fire stations"
    echo ${result}
    return ${result}
}

count_addresses ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE 'addr:housenumber' is not NULL" | tr -d ' '`"

    #echo "Found ${result} addresses"
    echo ${result}
    return ${result}
}

count_milestone ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE milestone is not NULL" | tr -d ' '`"

    #echo "Found ${result} milestones"
    echo ${result}
    return ${result}
}

count_hotspring ()
{
    cat <<EOF >> /tmp/foo-$$.sql
SELECT COUNT(*) FROM planet_osm_point WHERE "natural"='hot_spring' OR "leisure"='hot_spring' OR "amenity"='hot_spring' OR "natural"='hot_spring' OR 'bath:type'='hot_spring' OR name LIKE '%Hot%' ;
EOF
    local result="`psql --tuples-only --dbname=${database} -f /tmp/foo-$$.sql`"
    rm -f tmp/foo-$$.sql

    #echo "Found ${result} Hot springs"
    echo "${result}"
    return ${result}
}

count_trailhead ()
{    
    local result="`psql --tuples-only --dbname=${database} --command="SELECT count(*) FROM planet_osm_point WHERE amenity='parking' AND name LIKE '%Trailhead'" | tr -d ' '`"

    #echo "Found ${result} Trailheads"
    echo "${result}"
    return ${result}
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
	nws*)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,tags->'alt_name',tags->'addr:state',ST_AsKML(way) FROM planet_osm_line SORT WHERE boundary='administrative' AND name!='';
EOF
	    ;;
	road*)
	    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name,ST_AsKML(line.way),line.highway,line.surface,line.access,line.tags->'smoothness',line.tags->'tracktype',tags->'alt_name',tags->'4wd_only',service from planet_osm_line AS line WHERE (line.highway!='') AND (line.highway!='path' AND line.highway!='footway' AND line.highway!='cycleway');
EOF
	    ;;
	parcel*)
	    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name,ST_AsKML(line.way),line.tags->'addr:full',tags->'adrr:street',tags->'addr:housenumber',tags->'alt_name',tags->'addr:full' from planet_osm_line AS line;
EOF
	    ;;
	subdivision*)
	    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name,ST_AsKML(line.way) from planet_osm_line AS line;
EOF
	    ;;
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
SELECT line.osm_id,line.name,ST_AsKML(line.way),line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access FROM planet_osm_line AS line WHERE line.highway='footway' OR line.highway = 'path' OR line.highway = 'cycleway';
EOF
#		fi
#		cat <<EOF >> ${sqlout}
#SELECT planet_osm_line.osm_id,planet_osm_line.name,planet_osm_line.tags->'sac_scale',planet_osm_line.tags->'bicycle',planet_osm_line.tags->'mtb:scale:imba',planet_osm_line.access,ST_AsKML(planet_osm_line.way) FROM planet_osm_line,planet_osm_polygon WHERE ((planet_osm_line.highway = 'footway' OR planet_osm_line.highway = 'path') AND planet_osm_line.tags?'piste:type' != 't') ${polysql};
#EOF
	    ;;
	piste*)
	    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name,ST_AsKML(line.way),line.tags->'piste:type',line.tags->'piste:difficulty',line.tags->'piste:grooming',line.aerialway,line.access FROM planet_osm_line AS line WHERE line.tags->'piste:type' is not NULL
 OR line.aerialway='chair_lift';
EOF
# SELECT line.osm_id,line.name,line.tags->'piste:type',line.tags->'piste:difficulty',line.tags->'piste:grooming',line.aerialway,line.access,ST_AsKML(line.way) FROM planet_osm_line AS line, (SELECT name,way FROM planet_osm_polygon WHERE name='${folder}') AS poly WHERE (ST_Crosses(line.way,poly.way) OR ST_Contains(poly.way,line.way)) AND (line.tags?'piste:type' = 't' OR line.aerialway = 'chair_lift');
#		cat <<EOF >> ${sqlout}
#SELECT planet_osm_line.osm_id,planet_osm_line.name,planet_osm_line.tags->'piste:type',planet_osm_line.tags->'piste:difficulty',planet_osm_line.tags->'piste:grooming',planet_osm_line.aerialway,planet_osm_line.access,ST_AsKML(planet_osm_line.way) from planet_osm_line,planet_osm_polygon WHERE (planet_osm_line.tags?'piste:type' = 't' OR planet_osm_line.erialway = 'chair_lift');
#EOF
	    ;;
	trailhead)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way) from planet_osm_point WHERE (highway='trailhead' OR leisure='trailhead' OR amenity='trailhead') AND name LIKE '%Trailhead';
SELECT osm_id,name,ST_AsKML(way) from planet_osm_polygon WHERE amenity='parking' AND name LIKE '%Trailhead';
EOF
	    ;;
	camp*)
#	    SELECT name FROM planet_osm_polygon WHERE tags->'is_in'!='' AND tourism='camp_site';
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tags->'fee',tags->'toilets',tags->'website',tags->'operator',tags->'sites',amenity,leisure,tourism,tags->'is_in' from planet_osm_point WHERE tourism='camp_site' OR amenity='campground' ORDER BY tags->'is_in';
EOF
	    ;;
	milestone*)
	    # FIXME: Yes, this is a bad hack to hardcode the few roads we want mile markes for.
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tags->'alt_name' from planet_osm_point WHERE highway='milestone';
EOF
	    ;;
	historic)
#SELECT osm_id,name,ST_AsKML(way),historic from planet_osm_point WHERE historic='archaeological_site' OR historic='building' OR historic='ruins';
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),historic from planet_osm_point WHERE historic is not NULL;
EOF
	    ;;
	peak*)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),ele FROM planet_osm_point WHERE natural='peak';
EOF
	    ;;
	addr*)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,ST_AsKML(way),"addr:housenumber",tags->'addr:street',tags->'addr:full' FROM planet_osm_point WHERE tags->'addr:street'!='' AND 'addr:housenumber' is not NULL;
SELECT osm_id,ST_AsKML(ST_Centroid(way)),'addr:housenumber',tags->'addr:street',tags->'addr:full' FROM planet_osm_polygon WHERE tags->'addr:street'!='' AND 'addr:housenumber' is not NULL AND building='yes';
EOF
	    ;;
	hots*)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tags->'description' FROM planet_osm_point WHERE "natural"='hot_spring' OR "leisure"='hot_spring' OR "amenity"='hot_spring' OR 'bath:type'='hot_spring' OR name LIKE '%Hot%' ;
EOF
	    ;;
	helicopter)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tags->'emergency',tags->'aeroway' from planet_osm_point WHERE aeroway='helipad' OR aeroway='heliport' OR tags->'emergency'='landing_site' ${polysql};
EOF
	    ;;
	firewater)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tags->'emergency',tags->'fire_hydrant:type',tags->'fire_hydrant:diameter',water,tags->'water_tank:volume',tags->'note',disused,tags->'is_in' from planet_osm_point WHERE tags->'emergency'='fire_hydrant' OR tags->'emergency'='water_tank' ORDER BY tags->'is_in';
EOF
# 	    cat <<EOF >> ${sqlout}
# SELECT osm_id,name,ST_AsKML(way),tags->'emergency',tags->'fire_hydrant:type',tags->'fire_hydrant:diameter',water,tags->'water_tank:volume',tags->'note',disused,tags->'is_in' from planet_osm_point WHERE tags->'emergency'='fire_hydrant' OR tags->'emergency'='fire_water_pond' OR tags->'emergency'='suction_point' OR tags->'emergency'='water_tank';
# EOF
	    ;;
	emergency)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),amenity,tags->'emergency' from planet_osm_point WHERE tags->'emergency'!='';
EOF
	    ;;
	wifi)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way) from planet_osm_point WHERE tags->'internet_access'='wlan';
EOF
	    ;;
	waterfall*)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tags->'name.en',tags->'description' from planet_osm_point WHERE waterway='waterfall';
EOF
	    ;;
	swimming)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),name.en,description from planet_osm_point WHERE tags->'sport'='swimming' AND tags->'amenity'!='swimming_pool' ${polysql};
EOF
	    ;;
	climb)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),name.en,description from planet_osm_point WHERE tags->'sport'='climbing'' ${polysql};
EOF
	    ;;
	hut*)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber' from planet_osm_point WHERE tourism='wilderness_hut' OR tourism='alpine_hut' ${polysql};
EOF
	    ;;
	place*)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),place from planet_osm_point WHERE place='hamlet' OR place='village' OR place='town' OR place='isolated_dwelling' OR place='locality';
EOF
	    ;;
	lodging)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber',tags->'name:en' from planet_osm_point WHERE tourism='hotel' OR tourism='hostel' OR tourism='guest_house' ${polysql};
EOF
	    ;;
	*)
	    ;;
    esac

    echo ${sqlout}
    return 0
}
