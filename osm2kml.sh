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

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have cors signifying what type
# it is.
usage()
{
    echo "$0 database type"
    exit
}

if test $# -lt 1; then
    usage
fi

database="${1:-colorado}"
type="${2:-trails}"
tmpdir="/tmp"
outfile="${tmpdir}/${database}-${type}.kml"

if test -e ~/.mariadbrc; then
    source ~/.mariadbrc
fi

# KML Color chart
declare -A colors=()
colors[RED]="ff0000ff"
colors[BLACK]="ff000000"
colors[BLUE]="ffff0000"
colors[GREEN]="ff00ff00"
colors[CYAN]="ffffff00"
colors[MAGENTA]="ffff00ff"
colors[YELLOW]="ff00ffff"
colors[ORANGE]="ff00a5ff"
colors[PURPLE]="ff800080"
colors[LIGHTBLUE]="ffe6d8ad"
colors[DARKGREEN]="ff008000"
colors[GRAY]="ff888888"

# Our custom Icons for waypoints
icondir=icons
declare -A icons=()
icons[CAMPFIRE]="${icondir}/campfire.png"
icons[CAMPGROUND]="${icondir}/campground.png"
icons[PICNIC]="${icondir}/picnic.png"
icons[MOUNTAINS]="${icondir}/mountains.png"
icons[HIKER]="${icondir}/hiker.png"
icons[FIREDEPT]="${icondir}/firedept.png"

# Create the KML header
    cat <<EOF > ${outfile}
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2">
<Document>
    <name>${database} ${type}</name>
    <description></description>
    <visibility>1</visibility>
    <open>1</open>
EOF

# Setup the query as a string to avoid werd shell escaping syntax ugliness
sqlout="/tmp/query-${database}-${type}.sql"
if test ! -e "${sqlout}"; then
    case "${type}" in
	# We only want trails that aren't ski trails, as piste routes get different
	# colors. The only way we can tell the difference is if the piste:type tag
	# exists.
	trails)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,tags->'sac_scale',tags->'bicycle',tags->'mtb:scale',ST_AsKML(way) from planet_osm_line WHERE (highway = 'footway' OR highway = 'path') AND tags?'piste:type' != 't';
EOF
	    ;;
	piste)
	    cat <<EOF >> ${sqlout}
SELECT osm_id,name,tags->'piste:type',tags->'piste:difficulty',tags->'piste:grooming',aerialway,ST_AsKML(way) from planet_osm_line WHERE tags->'piste:type' = 'downhill' OR tags->'piste:type' = 'nordic' OR aerialway = 'chair_lift';
EOF
	    ;;
	roads|firestations|hospital)
	    ;;
	*)
	    ;;
    esac
fi

road_colors()
{
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
	    path|footway)
		color="${color:-YELLOW}"
		;;
	    cycleway|bridleway|track)
		color="${color:-YELLOW}"
		;;
	    *)
		color="${color:-RED}"
		echo "WARNING: unknown highway surface"
		;;
	esac
	case ${node[surface]} in
	    unpaved|asphalt|concrete|dirt|earth|grass|gravel_turf|fine_gravel|gravel|mud|ice) color="${color:-ORANGE}" ;;
	    *) ;;
	esac

    return 0
}

ski_color()
{
    local piste_type="$1"
    local piste_difficulty="$2"
    local piste_grooming="$3"
    local aerialway="$4"
    
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
    
    case ${piste_type} in
	downhill)
	    case ${piste_difficulty} in
		easy|novice) color="GREEN" ;;
		expert|advanced) color="BLACK" ;;
		intermediate) color="BLUE" ;;		
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
	snow_park)
	    color="PURPLE"
	    ;;
	*) ;;
    esac
    
    echo ${color}

    return 0
}

trail_color()
{
    local sac_scale="$1"
    local mtb_scale="$2"
    local mtb_scale="$3"

    local color="CYAN"
    
    # Mountain hiking scale
    case ${sac_scale} in
	hiking|mountain_hiking|alpine_hiking)
	    color="GREEN"
	    ;;
	demanding_mountain_hiking|demanding_alpine_hiking)
	    color="BLUE"
	    ;;
	difficult_mountain_hiking|difficult_alpine_hiking)
	    color="BLACK"
	    ;;
	*) ;;
    esac
	
    # Mountain Biking scales
    case ${mtb_scale_imba} in # 0-4
	0*) color="YELLOW" ;;
	1*) color="GREEN" ;;
	2*) color="BLUE" ;;
	3*) color="DARKGREEN" ;;
	4*) color="BLACK" ;;
	*)  ;;
    esac
    # http://wiki.openstreetmap.org/wiki/Key:mtb:scale
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

    echo "${color}"

    return 0
}

# Execute the query
data="/tmp/data-${database}-${type}.tmp"
#if test ! -e "${data}"; then
    time -p sudo -u postgres psql --dbname=${database} --no-align --file=${sqlout} --output=${data}
#fi
index=0
while read line; do
    id="`echo ${line} | cut -d '|' -f 1`"
    # Ignore the header row
    if test x"${id}" = x"osm_id"; then
	continue
    fi
    # The last line of the file is a count of rows. which we don't  need
    if test "`echo ${line} | grep -c "[0-9]* rows"`" -gt 0; then
	echo "Done processing file, processed ${index} nodes"
	break
    fi
    name="`echo ${line} | cut -d '|' -f 2 | sed -e 's:&:and:'`"
    case ${type} in
	 trails)
	     sac_scale="`echo ${line} | cut -d '|' -f 3`"
	     bicycle="`echo ${line} | cut -d '|' -f 4`"
	     mtb_scale="`echo ${line} | cut -d '|' -f 5`"
	     linestring="`echo ${line} | cut -d '|' -f 6`"
	     ways="`echo ${linestring:12} | cut -d '<' -f 1-3`"
	     color="`trail_color "${sac_scale}" "${mtb_scale}"`"
	     ;;
	 piste)
	     piste_type="`echo ${line} | cut -d '|' -f 3`"
	     piste_difficulty="`echo ${line} | cut -d '|' -f 4`"
	     piste_grooming="`echo ${line} | cut -d '|' -f 5`"
	     aerialway="`echo ${line} | cut -d '|' -f 6`"
	     linestring="`echo ${line} | cut -d '|' -f 7`"
	     ways="`echo ${linestring:12} | cut -d '<' -f 1-3`"
	     color="`ski_color "${piste_type}" "${piste_difficulty}" "${piste_grooming}" "${aerialway}"`"
	     ;;
	 roads|firestations|hospitals)
	     echo "ERROR ${type}: Not implemented yet!"
	     ::
    esac
    cat <<EOF >> ${outfile}
    <Placemark>
        <name>${name:-"Unknown Trail ${index}"}</name>
        <Style>
           <LineStyle>
             <width>3</width>
             <color>${colors[${color}]}</color>
           </LineStyle>
          </Style>
          <LineString>
            <tessellate>1</tessellate>
            <altitudeMode>clampToGround</altitudeMode>
            ${ways}
          </LineString>
    </Placemark>
EOF
    index="`expr ${index} + 1`"
# Google Maps has a limit of 5M or 2000 points
#    if test ${index} -gt 1999; then
#	break
#    fi
done < ${data}

    cat <<EOF >> ${outfile}
</Document>
</kml>
EOF
    
#rm -f ${data}
#rm -f ${sqlout}
