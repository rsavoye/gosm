#!/bin/bash

# 
#   Copyright (C) 2016, 2017   Free Software Foundation, Inc.
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
# for highways. Different types and surfaces have cors signifying what type
# it is.
usage()
{
    cat <<EOF
    $0 [options]
	--database(-d) database
        --subset(-s)   trails|piste|fire|lodging|wifi
        --polygon(-p)  existing polygon1,poly2,poly3
        --format(-f)   kml|kmz|aqm
        --title(-t)    title
        --output(-o)   output file name
        --name name1,name2,name3,...

    polygon can be multiple, seperated by a comma. Each gets it's own folder in
    the KML file.

    The optional name parameter is what the Folder gets called, and needs to be
    in the same order as the polygons.
EOF
    exit
}

if test $# -lt 1; then
    usage
fi

tourism=""
name=""
dbs="$1"
ns=""
outfile=""
polygon=""
subset="trails"
format="kml"
title=""
OPTS="`getopt -o d:h:t:f:s:n:o:p: -l database:,polygon:,subset:,format:,name:title:,output:,help`"
while test $# -gt 0; do
    case $1 in
        -d|--database) database=$2 ;;
        -s|--subset) subset=$2 ;;
        -f|--format) format=$2 ;;
        -p|--polygon) polys=$2, ;;
        -n|--name) ns=$2 ;;
        -t|--title) title=$2 ;;
        -o|--output) outfile=$2 ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

title="${title:-${database}-${subset}}"

case ${subset} in
    wifi|lodging|fire) type="waypoint" ;;
    *) type="line" ;;
esac

debug=yes

declare -a polygons=()
i=1
k=0
while test x"${polys}" != x; do
    poly="`echo ${polys} | cut -d ',' -f $i`"
    if test x"${poly}" = x; then
	break
    else
	polygons[$k]="${poly}"
    fi
    i="`expr $i + 1`"
    k="`expr $k + 1`"
done

i=0
declare -a names=()
if test -n "${ns}"; then
    for item in `echo ${ns} | tr ' ' '_' | tr ',' ' '`; do
	names[$i]="${item}"
	i="`expr $i + 1`"
    done
else
    for item in `echo ${database} | sed -e 's/,/ /'`; do
	names[$i]="${item}"
	i="`expr $i + 1`"
    done
fi

#tmpdir="$PWD"
tmpdir="/tmp"
outdir="${tmpdir}/tmp-$$"
mkdir -p ${outdir}
if test x"${outfile}" = x; then
    outfile="${tmpdir}/${database}-${subset}.${format}"
fi

rm -f /tmp/debug.log

if test -e ~/.mariadbrc; then
    source ~/.mariadbrc
fi

# KML Color chart
declare -A colors=()
opacity="ff"
colors[RED]="${opacity}0000ff"
colors[BLACK]="${opacity}000000"
colors[BLUE]="${opacity}ff0000"
colors[GREEN]="${opacity}00ff00"
colors[CYAN]="${opacity}ffff00"
colors[MAGENTA]="${opacity}ff00ff"
colors[YELLOW]="${opacity}00ffff"
colors[ORANGE]="${opacity}00a5ff"
colors[PURPLE]="${opacity}800080"
colors[LIGHTBLUE]="${opacity}e6d8ad"
colors[DARKGREEN]="${opacity}008000"
colors[GRAY]="${opacity}888888"

# Our custom Icons for waypoints
icondir=icons
declare -A icons=()
icons[HOSTEL]="#Hostel"
icons[HOTEL]="#Hotel"
icons[CASA]="#Casa"
icons[UNKNOWN]="#town"
icons[LODGING]="#Lodging"
icons[WIFI]="#Wifi"
icons[CAMPSITE]="#Campfire"
icons[CAMPGROUND]="#Campground"
icons[PICNIC]="#Picnic"
icons[MOUNTAINS]="#Mountains"
icons[HIKER]="#Hiker"
icons[FIRESTATION]="#FireStation"
icons[WATERTANK]="#WaterTowerOutline"
icons[CISTERN]="#Cistern"
icons[HYDRANT]="#Hydrant"
icons[WATER]="#Water"
icons[LANDINGSITE]="#Helicopter"
icons[PARKING]="#ParkingLot"
icons[TRAILHEAD]="#Trailhead"

get_icon()
{
    local tag="${1:-UNKNOWN}"
    local scale="${2:-1.0}"
    
#    underground) icon="icons[UNDERGRUND]" ;;
    
    cat <<EOF >> ${outfile}
        <Style>
	  <IconStyle>
	    <scale>${scale}</scale>
	    <Icon>
-	      <href>${icon[${tag}]}</href>
	    </Icon>
	  </IconStyle>
        </Style>
EOF

    return 0
}

road_colors()
{
    if test x"${debug}" = x"yes"; then
	echo "ski_color ($*)*" >> /tmp/debug.log
    fi
    # For highway surface typesq
    case ${node[highway]} in
	tertiary|service|gravel) # (like Upper Moon)
	    color="${color:-BLUE}"
	    ;;
	unclassified) # (like Rollins Pass)
	    color="${color:-BLACK}"
	    ;;
	road|residential|secondary|primary|trunk|motorway_link|trunk_link|secondary_link|teriary_link)
	    color="${color:-GREEN}"
	    ;;
	path|footway|surface)
	    color="${color:-YELLOW}"
	    ;;
	cycleway|bridleway|track)
	    color="${color:-YELLOW}"
	    ;;
	*)
	    color="${color:-RED}"
#	    echo "WARNING: unknown highway surface"
	    ;;
    esac
#    case ${node[surface]} in
#	unpaved|asphalt|concrete|dirt|earth|grass|gravel_turf|fine_gravel|gravel|mud|ice) color="${color:-ORANGE}" ;;
#	*) ;;
#    esac

    echo ${color}

    return 0
}

# http://wiki.openstreetmap.org/wiki/Piste_Maps#Type
ski_color()
{
    if test x"${debug}" = x"yes"; then
	echo "ski_color ($*)*" >> /tmp/debug.log
    fi
    local piste_type="$1"
    local piste_difficulty="$2"
    local piste_grooming="$3"
    local aerialway="$4"
    local access="$5"
    
    local color="BLACK"		# When in doubt, make it a back diamond

    # For skate skiing
    case ${piste_grooming} in
	classic) color="GREEN" ;;
	skating) color="GREEN" ;;
	classic+skating) color="GREEN" ;;
	backcountry) color="YELLOW" ;;
	*) ;;
    esac

    # For chairlifts
    case ${aerialway} in
	station)
	    echo "GREEN"
	    return 0
	    ;;
	chair_lift)
	    echo "RED"
	    return 0
	    ;;
	unknown|duration|occupancy)
	    echo "PURPLE"
	    return 0
	    ;;
	*)
	    ;;
    esac

    # For US, Canada,and Oceania
    #	novice|easy =green,
    #	intermediate=blue,
    #	advanced|expert=black,
    #	freeride=yellow.
    #
    # For Europe
    #	novice|easy=green
    #	intermediate=red
    #	advanced=black
    #	expert=orange
    #	freeride=yellow
    case ${piste_type} in
	downhill)
	    case ${piste_difficulty} in
		easy|novice) color="GREEN" ;;
		expert|advanced) color="BLACK" ;;
		intermediate) color="BLUE" ;;
		freeride) color="YELLOW" ;;
		extreme) color="BLACK" ;;
		*) ;;
	    esac
	    ;;
	nordic|skitour)
	    case ${piste_difficulty} in
		easy|novice) color="CYAN" ;;
		expert|advanced) color="GRAY" ;;
		intermediate) color="LIGHTBLUE" ;;		
		skating) color="YELLOW" ;;
		classic+skating) color="GREEN" ;;
		*) ;;
	    esac
	    ;;
	snow_park|sled|sleigh|hike)
	    color="PURPLE"
	    ;;
	*) ;;
    esac
    
    echo ${color}

    return 0
}

trail_color()
{
    if test x"${debug}" = x"yes"; then
	echo "trail_color ($*)" >> /tmp/debug.log
    fi

    local sac_scale="$1"
    local mtb_scale_imba="$2"
    local access="$3"

    local color="MAGENTA"	# default color

    # http://wiki.openstreetmap.org/wiki/Key:sac_scale
    # hiking = Trail well cleared
    # mountain_hiking - Trail with continuous line and balanced ascent
    # demanding_mountain_hiking - exposed sites may be secured with ropes or chains,
    #                             possible need to use hands for balance
    # Mountain hiking scale
    if test x"${sac_scale}" != x; then
	case ${sac_scale} in
	    hiking) color="YELLOW" ;;
	    mountain_hiking|demanding_mountain_hiking) color="RED" ;;
	    alpine_hiking|difficult_alpine_hiking|demanding_alpine_hiking) color="BLUE" ;;
	    *) color="PURPLE" ;;
	esac
    fi

    # GaiaGPS uses these colors:
    # green - Aspen Alley
    # Orange - Re-Root
    # blue - Hobbit Trail
    # yellow - School Bus
    # cyan - Sugar Mag
    # purple - Lookout Trail
    #
    # MTB Project uses
    # Aspen Alley (blue square with black dot) intermediate, difficult
    # Re-Root (blue square with black dot)
    # Hobbit Trail (blue square)
    # School Bus (blue square) Intermediate
    # Sugar Mag (black diamond) difficult
    # Lookout Trail (blue square)
    # IMBA
    # easiest - white
    # easy - green
    # intermediate - blue
    # difficult - black
    # expert - double black

    # Mountain Biking scales. Make the hiking rating more important
    # since we hike into an emergency, we don't ride bikes.
    if test x"${mtb_scale_imba}" != x -a x"${sac_scale}" = x; then
	case ${mtb_scale_imba} in # 0-4
	    0*) color="YELLOW" ;; # easiest
	    1*) color="GREEN" ;;  # easy
	    2*) color="BLUE" ;;   # intermediate
	    3*) color="BLACK" ;;  # difficult
	    4*) color="PURPLE" ;; # double black
	    *)  ;;
	esac
    fi
    # http://wiki.openstreetmap.org/wiki/Key:mtb:scale
    if test x"${mtb_scale}" != x  -a x"${sac_scale}" = x; then
	case ${mtb_scale} in # 0-6
	    0*) color="YELLOW" ;;
	    1*) color="GREEN" ;;
	    2*) color="LIGHTBLUE" ;;
	    3*) color="BLUE" ;;
	    4*) color="DARKGREEN" ;;
	    5*) color="PURPLE" ;;
	    6*) color="BLACK" ;;
	    *)  ;;
	esac
    fi
    
    echo "${color}"
    return 0
}

cat <<EOF > ${outfile}
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2">
<Document>
    <name>${title}</name>
    <visibility>1</visibility>
    <open>1</open>
EOF

cat `dirname $0`/styles.xml >> ${outfile}

i=0
# Execute the query
while test $i -lt ${#polygons[@]} -o x"${type}" = x"waypoint"; do
    folder="`basename ${polygons[$i]:-${subset}} | sed -e 's:\.[a-z]*::'`"
    echo "Processing ${folder}..."

    # See if the polygon exists in the database. If not we obviously can't
    # use it.
    rows=
    if test "`echo ${polygons[$i]} | grep -c poly`" -eq 0 -a x"${type}" != x"waypoint"; then
	rows=`psql --dbname=${database} --command="SELECT name FROM planet_osm_polygon WHERE name='${folder}'" | grep " row" | grep -o "[0-9]"`

	if test ${rows} -eq 0; then
	    echo "ERROR: ${folder} doesn't exist in planet_osm_polygon!"
	    i="`expr $i + 1`"
	    continue
	else
	    echo "${folder} exists in planet_osm_polygon"
	fi
    fi
    
    # Setup the query as a string to avoid werd shell escaping syntax ugliness
    sqlout="`echo /tmp/query-${folder}-${type}.sql | tr ' ' '-'`"
    rm -f ${sqlout}
    #    select osm_id INTO wifi FROM planet_osm_point WHERE tags->'internet_access'='wlan';
    # select osm_id FROM planet_osm_point WHERE tourism='guest_house' OR tourism='hotel' OR tourism='hostel'
#    rm -f ${sqlout}
    if test ! -e "${sqlout}"; then
	case "${subset}" in
	    # We only want trails that aren't ski trails, as piste routes get different
	    # colors. The only way we can tell the difference is if the piste:type tag
	    # exists.
	    trails)
#		cat <<EOF >> ${sqlout}
#SELECT line.osm_id,line.name,line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access,ST_AsKML(line.way) FROM planet_osm_line AS line, dblink('dbname=polygons', 'select name,geom FROM boundary') AS poly(name name,geom geometry) WHERE poly.name='${polygon}' AND (ST_Crosses(line.way,poly.geom) OR ST_Contains(poly.geom,line.way)) AND (line.highway='footway' OR line.highway = 'path');
#EOF
		# Works!
		if test "`echo ${polygons[$i]} | grep -c poly`" -eq 0; then
		    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name,line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access,ST_AsKML(line.way) FROM planet_osm_line AS line, (SELECT name,way FROM planet_osm_polygon WHERE name='${folder}') AS poly WHERE (ST_Crosses(line.way,poly.way) OR ST_Contains(poly.way,line.way)) AND (line.highway='footway' OR line.highway = 'path');
EOF
		else
		    cat <<EOF >> ${sqlout}
SELECT line.osm_id,line.name,line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access,ST_AsKML(line.way) FROM planet_osm_line AS line WHERE line.highway='footway' OR line.highway = 'path';
EOF
		fi
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
	    waypoint)
		cat <<EOF >> ${sqlout}
SELECT osm_id,name,tags->'emergency',amenity,highway,tourism,tags->'fire_hydrant:type',ST_AsKML(way) from planet_osm_point' ${polysql};
EOF
		;;
	    wifi)
		cat <<EOF >> ${sqlout}
SELECT osm_id,name,ST_AsKML(way) from planet_osm_point WHERE tags->'internet_access'='wlan' ${polysql};
EOF
		;;
	    lodging)
		cat <<EOF >> ${sqlout}
SELECT osm_id,name,tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber',ST_AsKML(way) from planet_osm_point WHERE tourism='guest_house' OR tourism='hotel' OR tourism='hostel' ${polysql};
EOF
		;;
	    roads)
		cat <<EOF >> ${sqlout}
SELECT osm_id,name,highway,ST_AsKML(way) from planet_osm_line WHERE highway='secondary' OR highway='tertiary' OR highway='unclassified' OR highway='residential' OR highway='service' OR planet_osm_line.highway='track';
EOF
		;;
	    firestations|hospital)
		;;
	    *)
		;;
	esac
    fi
# select planet_osm_line.name FROM dblink('dbname=polygons', 'select name,geom from boundary') AS t1(name name,geometry geometry),planet_osm_line WHERE t1.name='VAIL' OR (ST_Contains(t1.geometry,planet_osm_line.way) OR ST_Crosses(t1.geometry,planet_osm_line.way));

    name="`echo ${names[$i]} | tr '_' ' '`"
    echo "    <Folder>" >> ${outfile}
    echo "        <name>${name}</name>" >> ${outfile}
    
    data="`echo ${outdir}/data-${folder}-${type}.tmp | tr ' ' '-'`"
    psql --dbname=${database} --no-align --file=${sqlout} --output=${data}
    index=0
    while read line; do
	if test x"${debug}" = x"yes"; then
	    echo "line: ${line}" | sed -e 's:LineString..*::' >> /tmp/debug.log
	fi
	id="`echo ${line} | cut -d '|' -f 1`"
	# Ignore the header row
	if test x"${id}" = x"osm_id"; then
	    continue
	fi
	# The last line of the file is a count of rows. which we don't need
	if test "`echo ${line} | grep -c "[0-9]* rows"`" -gt 0; then
	    echo "Done processing file, processed ${index} nodes"
	    break
	fi
	name="`echo ${line} | sed -e 's:Rent|::' | cut -d '|' -f 2 | sed -e 's:&:and:'`"
	declare -a description=()
	case ${subset} in
	    wifi)
		way="`echo ${line} | cut -d '|' -f 3`"
		;;
	    lodging)
		line="`echo ${line} | sed -e 's:Rent|::'`"
		tourism="`echo ${line} | cut -d '|' -f 3`"
		phone="`echo ${line} | cut -d '|' -f 4`"
		email="`echo ${line} | cut -d '|' -f 5`"
		website="`echo ${line} | cut -d '|' -f 6`"
		street="`echo ${line} | cut -d '|' -f 7`"
		housenumber="`echo ${line} | cut -d '|' -f 8`"
		way="`echo ${line} | cut -d '|' -f 9`"
		if test x"${phone}" != x; then
		    description=("Phone: ${phone}" "${description[@]}")
		fi
		if test x"${street}" != x; then
		    description=("Street: ${street}" "${description[@]}")
		fi
		if test x"${housenumber}" != x; then
		    description=("Housenumber: ${housenumber}" "${description[@]}")
		fi
		if test x"${email}" != x; then
		    description=("Email: ${email}" "${description[@]}")
		fi
		if test x"${website}" != x -a `echo ${website} | grep -c '?'` -eq 0; then
		    description=("Website: ${website}" "${description[@]}")
		fi
		;;
	    waypoint)
		#	    emergency="`echo ${line} | cut -d '|' -f 3`"
		#	    amenity="`echo ${line} | cut -d '|' -f 4`"
		#	    highway="`echo ${line} | cut -d '|' -f 5`"
		#	    tourism="`echo ${line} | cut -d '|' -f 6`"
		#	    hydrant="`echo ${line} | cut -d '|' -f 3`"
		linestring="`echo ${line} | cut -d '|' -f 7`"
		way="`echo ${linestring:12} | cut -d '<' -f 1-3`"
		emergency=""
		if test x"${emergency}" != x; then
		    description=("Emergency: ${emergency}" "${description[@]}")
		fi
		;;
	    trails)
		sac_scale="`echo ${line} | cut -d '|' -f 3`"
		bicycle="`echo ${line} | cut -d '|' -f 4`"
		mtb_scale="`echo ${line} | cut -d '|' -f 5`"
		access="`echo ${line} | cut -d '|' -f 6`"
		linestring="`echo ${line} | cut -d '|' -f 7`"
		ways="`echo ${linestring:12} | cut -d '<' -f 1-3`"
		color="`trail_color "${sac_scale}" "${mtb_scale}" "${access}"`"
		if test x"${sac_scale}" != x; then
		    description=("SAC Scale: ${sac_scale}" "${description[@]}")
		fi
		if test x"${mtb_scale}" != x; then
		    description=("MTB Scale: ${mtb_scale}" "${description[@]}")
		fi
#		if test x"${access}" != x; then
#		    description="${description}Access: ${access}"
#		fi
		;;
	    piste)
		piste_type="`echo ${line} | cut -d '|' -f 3`"
		piste_difficulty="`echo ${line} | cut -d '|' -f 4`"
		piste_grooming="`echo ${line} | cut -d '|' -f 5`"
		aerialway="`echo ${line} | cut -d '|' -f 6`"
		access="`echo ${line} | cut -d '|' -f 7`"
		linestring="`echo ${line} | cut -d '|' -f 8`"
		ways="`echo ${linestring:12} | cut -d '<' -f 1-3`"
		color="`ski_color "${piste_type}" "${piste_difficulty}" "${piste_grooming}" "${aerialway}" "${access}"`"
		;;
	    roads|firestations|hospitals)
		highway="`echo ${line} | cut -d '|' -f 3`"
		linestring="`echo ${line} | cut -d '|' -f 4`"
		ways="`echo ${linestring:12} | cut -d '<' -f 1-3`"
		color="`road_colors "${highway}"`"
		description=
		if test x"${highway}" != x; then
		    description="${description}Type: ${highway}<br>"
		fi
		;;
	esac
	newcolor="`echo ${color} | tr '[:upper:]' '[:lower:]'`"

	case ${type} in
	    line)
		cat <<EOF >> ${outfile}
        <Placemark>
            <name>${name:-"Unknown Trail ${index}"}</name>
EOF
		# The description may have multiple lines.
		if test "${#description[@]}" -gt 0; then
		    echo "            <description>"  >> ${outfile}
		    j=0
		    while test $j -lt ${#description[@]}; do
			echo "${description[$j]}" >> ${outfile}
			j="`expr $j + 1`"
		    done
		    echo "            </description>"  >> ${outfile}
		fi
		lowcolor="`echo ${color} | tr '[:upper:]' '[:lower:]'`"
		cat <<EOF >> ${outfile}
	      <styleUrl>#line_${lowcolor}</styleUrl>
              <LineString>
                <tessellate>1</tessellate>
                <altitudeMode>clampToGround</altitudeMode>
                ${ways}
              </LineString>
        </Placemark>
EOF
		;;
	    waypoint)
		case ${tourism} in
		    guest_house) idx="CASA" ;;
		    hotel) idx="HOTEL" ;;
		    hostel) idx="HOSTEL" ;;
		    *) idx="`echo ${subset} | tr '[:lower:]' '[:upper:]'`" ;;
		esac
		cat <<EOF >> ${outfile}
        <Placemark>
            <name>${name:-"Unknown ${id}"}</name>
            <styleUrl>${icons[${idx}]}</styleUrl>
EOF
		echo "FOO ${#description[@]}"
		# The description may have multiple lines.
		if test "${#description[@]}" -gt 0; then
		    echo "            <description>"  >> ${outfile}
		    j=0
		    while test $j -lt ${#description[@]}; do
			echo "${description[$j]}" >> ${outfile}
			j="`expr $j + 1`"
		    done
		    echo "            </description>"  >> ${outfile}
		fi
		cat <<EOF >> ${outfile}
            ${way}
        </Placemark>
EOF
		;;
	    *)
		echo "ERROR: ${type} unknown!"
		exit
		;;
	esac
    done < ${data}
    if test ${#polygons[@]} -gt 1 -o x"${type}" = x"waypoint"; then
	echo "    </Folder>" >> ${outfile}
    fi
    i="`expr $i + 1`"
    if test x"${type}" = x"waypoint"; then
	break
    fi
done

cat <<EOF >> ${outfile}
</Document>
</kml>
EOF

if test x"${format}" = x"kmz"; then
    mkdir -p ${outdir}
    cp -r icons ${outdir}/
    newout="${tmpdir}/$1-${type}.kmz"
fi

#rm -f ${data}
#rm -f ${sqlout}

echo "KML file is ${outfile}"
echo "SQL file is ${sqlout}"
