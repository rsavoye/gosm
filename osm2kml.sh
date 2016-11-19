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
    cat <<EOF
    $0 [options]
	--database(-d) db1,db2,db3,...
        --type trails|piste|waypoint
        --format(-f) kml|kmz
        --name name1,name2,name3,...

    database can be multiple, seperated by a comma. Each gets it's own folder in
    the KML file.

    The optional name parameter is what the Folder gets called, and needs to be
    in the same order as the databases.
EOF
    exit
}

if test $# -lt 1; then
    usage
fi

name=""
dbs="$1"
ns=""
OPTS="`getopt -o d:h:t:f:i:n -l database:,type:,format:,name:title:,help`"
while test $# -gt 0; do
    case $1 in
        -d|--database) dbs=$2 ;;
        -t|--type) dbs=$2 ;;
        -f|--format) format=$2 ;;
        -n|--name) ns=$2 ;;
        -i|--title) title=$2 ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

type="${ype:-trails}"
format="${format:-kml}"
title="${title:-${dbs}-${type}}"

debug=yes

declare -a databases=()
i=0
for db in `echo ${dbs} | sed -e 's/,/ /'`; do
    databases[$i]="${db}"
    i="`expr $i + 1`"
done

i=0
declare -a names=()
if test -n "${ns}"; then
    for item in `echo ${ns} | tr ' ' '_' | sed -e 's/,/ /'`; do
	names[$i]="${item}"
	i="`expr $i + 1`"
    done
else
    for item in `echo ${dbs} | sed -e 's/,/ /'`; do
	names[$i]="${item}"
	i="`expr $i + 1`"
    done
fi

#tmpdir="$PWD"
tmpdir="/tmp"
outdir="${tmpdir}/tmp-$$"
mkdir -p ${outdir}
if test x"${format}" = x"kml"; then
    outfile="${tmpdir}/${dbs}-${type}.kml"
else
    outfile="${outdir}/doc.kml"
fi


rm -f /tmp/debug.log

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
icons[CAMPSITE]="${icondir}/campfire.png"
icons[CAMPGROUND]="${icondir}/campground.png"
icons[PICNIC]="${icondir}/picnic.png"
icons[MOUNTAINS]="${icondir}/mountains.png"
icons[HIKER]="${icondir}/hiker.png"
icons[FIRESTATION]="${icondir}/firedept.png"
icons[WATERTANK]="${icondir}/WaterTowerOutline.png"
icons[UNDERGROUND]="${icondir}/cistern.png"
icons[PILLAR]="${icondir}/FireHydrant.png"
icons[LANDINGSITE]="${icondir}/Helicopter.png"
icons[PARKING]="${icondir}/parking_lot.png"
icons[TRAILHEAD]="${icondir}/Trailhead.png"
icons[WAY]="${icondir}/"

get_icon()
{
    local emergency="`echo ${line} | cut -d '|' -f 3`"
    local amenity="`echo ${line} | cut -d '|' -f 4`"
    local highway="`echo ${line} | cut -d '|' -f 5`"
    local tourism="`echo ${line} | cut -d '|' -f 6`"
    local hydrant="`echo ${line} | cut -d '|' -f 3`"
    local linestring="`echo ${line} | cut -d '|' -f 7`"
    local ways="`echo ${linestring:12} | cut -d '<' -f 1-3`"
    local icon=

    case ${highway} in
	trailhead) icon="icons[TRAILHEAD]" ;;
    esac

    case ${amenity} in
	parking) icon="icons[PARKONG]" ;;
    esac

    case ${emergency} in
	fire_hydrant) icon="icons[FIREHYDRANT]" ;;
	fire_station) icon="icons[FIRESTATION]" ;;
	water_tank) icon="icons[WATERTANK]" ;;
	landing_site) icon="icons[LANDINGSITE]" ;;
    esac

    case ${tourism} in
	camp_site) icon="icons[CAMPSITE]" ;;
	picnic_site) icon="icons[PICNIC]" ;;
    esac

    case ${hydrant} in
	underground) icon="icons[UNDERGRUND]" ;;
	pillar) icon="icons[PILLAR]" ;;
	way) icon="icons[WAY]" ;;
    esac

    cat <<EOF >> ${outfile}
	<IconStyle>
	  <scale>1.0</scale>
	  <Icon>
-	    <href>icons/${icon}</href>
	  </Icon>
	</IconStyle>
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
    local mtb_scale="$2"
    local mtb_scale="$3"
    local access="$4"

    local color="MAGENTA"

    # http://wiki.openstreetmap.org/wiki/Key:sac_scale
    # Mountain hiking scale
    case ${sac_scale} in
	hiking) color="YELLOW" ;;
	mountain_hiking|demanding_mountain_hiking) color="RED" ;;
	alpine_hiking|difficult_alpine_hiking|demanding_alpine_hiking) color="BLUE" ;;
	*) color="PURPLE" ;;
    esac

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

    # Mountain Biking scales
    case ${mtb_scale_imba} in # 0-4
	0*) color="YELLOW" ;; # easiest
	1*) color="GREEN" ;;  # easy
	2*) color="BLUE" ;;   # intermediate
	3*) color="BLACK" ;;  # difficult
	4*) color="PURPLE" ;; # double black
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

cat <<EOF > ${outfile}
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2">
<Document>
    <name>${title}</name>
    <description></description>
    <visibility>1</visibility>
    <open>1</open>
    <Style id="line_red">
        <LineStyle>
            <color>ff0000ff</color>
            <width>5</width>
        </LineStyle>
        <LabelStyle>
            <color>ff0000ff</color>
        </LabelStyle>
    </Style>
    <Style id="line_green">
        <LineStyle>
            <color>ff00ff00</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_black">
        <LineStyle>
            <color>ff000000</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_blue">
        <LineStyle>
            <color>ffff0000</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_orange">
        <LineStyle>
            <color>ff00a5ff</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_yellow">
        <LineStyle>
            <color>ff00ffff</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_cyan">
        <LineStyle>
            <color>ffffff00</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_magenta">
        <LineStyle>
            <color>ffff00ff</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_purple">
        <LineStyle>
            <color>ff800080</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_gray">
        <LineStyle>
            <color>ff888888</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_lightblue">
        <LineStyle>
            <color>ffe6d8ad</color>
            <width>5</width>
        </LineStyle>
    </Style>
    <Style id="line_darkgreen">
        <LineStyle>
            <color>ff008000</color>
            <width>5</width>
        </LineStyle>
    </Style>
EOF

i=0
# Execute the query
for folder in ${databases[@]}; do
    # Create the KML header

    # Setup the query as a string to avoid werd shell escaping syntax ugliness
    sqlout="/tmp/query-${folder}-${type}.sql"
    if test ! -e "${sqlout}"; then
	case "${type}" in
	    # We only want trails that aren't ski trails, as piste routes get different
	    # colors. The only way we can tell the difference is if the piste:type tag
	    # exists.
	    trails)
		cat <<EOF >> ${sqlout}
SELECT osm_id,name,tags->'sac_scale',tags->'bicycle',tags->'mtb:scale',access,ST_AsKML(way) from planet_osm_line WHERE (highway = 'footway' OR highway = 'path') AND tags?'piste:type' != 't';
EOF
		;;
	    piste)
		cat <<EOF >> ${sqlout}
SELECT osm_id,name,tags->'piste:type',tags->'piste:difficulty',tags->'piste:grooming',aerialway,access,ST_AsKML(way) from planet_osm_line WHERE tags?'piste:type' = 't' OR aerialway = 'chair_lift';
EOF
		;;
	    waypoint)
		cat <<EOF >> ${sqlout}
SELECT osm_id,tags->'emergency',amenity,highway,tourism,tags->'fire_hydrant:type',ST_AsKML(way) from planet_osm_point';
EOF
		;;
	    roads)
		cat <<EOF >> ${sqlout}
SELECT osm_id,name,highway,ST_AsKML(way) from planet_osm_line WHERE highway='secondary' OR highway='tertiary' OR highway='unclassified' OR highway='residential' OR highway='service' OR highway='track';
EOF
		;;
	    firestations|hospital)
		;;
	    *)
		;;
	esac
    fi

    echo "FOO"
    declare -p names
    name="`echo ${names[$i]} | tr '_' ' '`"
    echo "    <Folder>" >> ${outfile}
    echo "        <name>${name}</name>" >> ${outfile}

    data="${outdir}/data-${folder}-${type}.tmp"
    #if test ! -e "${data}"; then
    time -p psql --dbname=${folder} --no-align --file=${sqlout} --output=${data}
    #fi
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
	# The last line of the file is a count of rows. which we don't  need
	if test "`echo ${line} | grep -c "[0-9]* rows"`" -gt 0; then
	    echo "Done processing file, processed ${index} nodes"
	    break
	fi
	name="`echo ${line} | cut -d '|' -f 2 | sed -e 's:&:and:'`"
	case ${type} in
	    waypoint)
		#	    emergency="`echo ${line} | cut -d '|' -f 3`"
		#	    amenity="`echo ${line} | cut -d '|' -f 4`"
		#	    highway="`echo ${line} | cut -d '|' -f 5`"
		#	    tourism="`echo ${line} | cut -d '|' -f 6`"
		#	    hydrant="`echo ${line} | cut -d '|' -f 3`"
		linestring="`echo ${line} | cut -d '|' -f 7`"
		way="`echo ${linestring:12} | cut -d '<' -f 1-3`"
		;;
	    trails)
		sac_scale="`echo ${line} | cut -d '|' -f 3`"
		bicycle="`echo ${line} | cut -d '|' -f 4`"
		mtb_scale="`echo ${line} | cut -d '|' -f 5`"
		access="`echo ${line} | cut -d '|' -f 6`"
		linestring="`echo ${line} | cut -d '|' -f 7`"
		ways="`echo ${linestring:12} | cut -d '<' -f 1-3`"
		color="`trail_color "${sac_scale}" "${mtb_scale}" "${access}"`"
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
		::
	esac
	newcolor="`echo ${color} | tr '[:upper:]' '[:lower:]'`"
	#             <color>${colors[${color}]}</color>
	#           <styleUrl>#line_${newcolor}</styleUrl>
	#            <styleUrl>#line_${color}</styleUrl>
	#           <LineStyle>
	#             <width>3</width>
	#             <color>${colors[${color}]}</color>
	#            </LineStyle>

	if test x"${format}" = x"kml"; then
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
	else
	    cat <<EOF >> ${outfile}
        <Placemark>
            <name>${name:-"Unknown Location ${index}"}</name>
EOF
            get_icon ${line}

	    cat <<EOF >> ${outfile}
            <Point>
                ${way}
            </Point>
        </Placemark>
EOF
	fi
	index="`expr ${index} + 1`"
	# Google Maps has a limit of 5M or 2000 points
	#    if test ${index} -gt 1999; then
	#	break
	#    fi
    done < ${data}
    echo "    </Folder>" >> ${outfile}
    i="`expr $i + 1`"
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
