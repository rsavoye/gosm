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
# for highways. Different types and surfaces have tags signifying what type
# it is.

# load commonly used functions
osmbin="`which $0`"
topdir="`dirname ${osmbin}`"
. "${topdir}/osmshlib/parse.sh" || exit 1
. "${topdir}/osmshlib/sql.sh" || exit 1
. "${topdir}/osmshlib/kml.sh" || exit 1
. "${topdir}/osmshlib/colors.sh" || exit 1

# Include the darabase access user and password
if test -e ~/.mariadbrc; then
    source ~/.mariadbrc
fi

#set -o nounset                              # Treat unset variables as an error

# This is a list of supported subsets of data to extract.
supportedlines="trails piste roads"
supportedpoints="firewater emergency lodging wifi waterfall swimming"
supported="${supportedlines} ${supportedpoints}"

usage()
{
    local sup="`echo ${supported} | sed -e 's/ /[:name],/g'`"
    
    cat <<EOF
    $0 [options]
	--database(-d) database 
        --subset(-s)   (${sup})
        --polygon(-p)  existing polygon1[:name],poly2[:name],poly3[:name]
        --format(-f)   kml|kmz|aqm
        --title(-t)    title
        --output(-o)   output file name

    Multiple polygons or data seubets can be specified. The optionsl :name is used
    for the Folder name imstead of defaulting to the polygon or database name.
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
OPTS="`getopt -o d:h:t:f:s:o:p: -l database:,polygon:,subset:,format:,title:,output:,help`"
while test $# -gt 0; do
    case $1 in
        -d|--database) database=$2 ;;
        -s|--subset) subs=$2 ;;
        -f|--format) format=$2 ;;
        -p|--polygon) polys=$2, ;;
        -t|--title) title=$2 ;;
        -o|--output) outfile=$2 ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

title="${title:-${database} `echo ${subs} | sed -e 's/:[a-zA-Z0-9]*//'`}"
# Always use a full path
if test `dirname ${outfile}`; then
    outfile="$PWD/${outfile}"
fi

# Process the list of data subsets
declare -a subsets
declare -a subnames
declare -a subtypes
i=1				# array indexes can't start with 0
subs="`echo ${subs} | tr ',' ' '`"
for sub in ${subs}; do
    subsets[$i]="`echo ${sub} | cut -d ':' -f 1`"
    if test "`echo ${supported} | grep -c ${subsets[$i]}`" -eq 0; then
	echo "ERROR: ${sub} not supported!"
	continue
    fi
    subnames[$i]="`echo ${sub} | cut -d ':' -f 2`"
    if test x"${subnames[$i]}" = x; then
	subnames[$i]="${sub}"
    fi
    case ${subsets[$i]} in
	wifi|lodging|fire|waterfall|swimming) subtypes[$i]="waypoint" ;;
	*) subtypes[$i]="line" ;;
    esac
    i="`expr $i + 1`"
done

debug=yes

# Process the list of polygons
declare -a polygons=()
declare -a polynames=()
i=1				# array indexes can't start with 0
polys="`echo ${polys} | tr ',' ' '`"
for poly in ${polys}; do
    polygons[$i]="`echo ${polys} | cut -d ':' -f 1`"
    polynames[$i]="`echo ${polys} | cut -d ':' -f 2`"
    if test x"${polynames[$i]}" = x; then
	polynames[$i]="${poly}"
    fi
    i="`expr $i + 1`"
done

#tmpdir="$PWD"
tmpdir="/tmp"
outdir="${tmpdir}/osmtmp-$$"
mkdir -p ${outdir}
if test x"${outfile}" = x; then
    outfile="${outdir}/${database}-${subs}.kml"
fi

rm -f /tmp/debug.log

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
icons[WATERFALL]="#Waterfall"
icons[SWIMMING]="#Swimming"
icons[LANDINGSITE]="#Helicopter"
icons[PARKING]="#ParkingLot"
icons[TRAILHEAD]="#Trailhead"

get_icon()
{
    local tag="${1:-UNKNOWN}"
    local scale="${2:-1.0}"
    
#    underground) icon="icons[UNDERGROUND]" ;;
    
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

# Make sure the specified polygon is in the database
if test ${#polygons[@]} -gt 0; then
    for i in ${!#polygons[@]}; do
	echo "Processing ${polynames[$i]}..."
	poly_exists ${polygons[$i]}
	if test $? -gt 0; then
	    echo "ERROR: ${polynames[$i]} doesn't exist in planet_osm_polygon!"
	else
	    echo "${polynames[$i]} exists in planet_osm_polygon!"
	fi
    done
fi

# Create the final KML file
kml_file_header ${outfile} "${title}"

# Execute the query
for i in ${!subsets[@]}; do
    # Create the SQL command file
    sqlcmd="`sql_file ${subsets[$i]} ${outdir}/${database}-${subsets[$i]}`"
    sqlout="`echo ${sqlcmd} | sed -e 's:\.sql:.tmp:'`"
    kmlout="`echo ${sqlcmd} | sed -e 's:\.sql:.kml:'`"
    name="`echo ${subnames[$i]} | tr '_' ' '`"

    kml_folder_start ${kmlout} "${name}"

    # execute the query
    psql --tuples-only --dbname=${database} --no-align --file=${sqlcmd} --output=${sqlout}
    index=0
    func="parse_${subsets[$i]}"
	
    while read line; do
	if test x"${debug}" = x"yes"; then
	    echo "line: ${line}" | sed -e 's:LineString..*::' >> /tmp/debug.log
	fi
	id="`echo ${line} | cut -d '|' -f 1`"
	# Bleech, ugly hack to fix errors in strings that screw up parsing.
	name="`echo ${line} | sed -e 's:Rent|::' | cut -d '|' -f 2 | sed -e 's:\&:and:'`"
	way="`echo ${line} | cut -d '|' -f 3`"
	out="`${func} "${line}"`"
	eval $out
	echo "BARFOO: `declare -p data`"
	kml_placemark ${kmlout} "`declare -p data`"
#	newcolor="`echo ${color} | tr '[:upper:]' '[:lower:]'`"
# 		cat <<EOF >> ${sqlout}
# 	      <styleUrl>#line_${lowcolor}</styleUrl>
#               <LineString>
#                 <tessellate>1</tessellate>
#                 <altitudeMode>clampToGround</altitudeMode>
#                 ${ways}
#               </LineString>
#         </Placemark>
# EOF
    done < ${sqlout}
    kml_folder_end ${kmlout}
done

cat ${outdir}/*.kml >> ${outfile}
kml_file_footer ${outfile}

echo "SQL file is ${sqlcmd}"
if test x"${format}" = x"kmz"; then
    newout="`basename ${outfile} | sed -e 's:\.kml:.kmz:'`"
    (cd ${topdir} && zip -r ${outdir}/${newout} icons)
    zip -j ${outdir}/${newout} ${outfile}
    echo "KMZ file is ${outdir}/${newout}"
fi

rm -fr ${outdir}/*.tmp ${outdir}/*.sql

