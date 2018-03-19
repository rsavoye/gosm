#!/bin/bash

# 
#   Copyright (C) 2016, 2017, 2018   Free Software Foundation, Inc.
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
. "${topdir}/osmshlib/colors.sh" || exit 1
. "${topdir}/osmshlib/parse.sh" || exit 1
. "${topdir}/osmshlib/sql.sh" || exit 1
. "${topdir}/osmshlib/kml.sh" || exit 1

#set -o nounset                              # Treat unset variables as an error

# This is a list of supported subsets of data to extract.
supportedlines="trails piste roads"
supportedpoints="emergency lodging huts wifi waterfall swimming historic camp trailhead peak hotspring firewater helicopter milestone addresses"
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
        --extra(-e)    extra tags
        --output(-o)   output file name

    Multiple polygons or data subsets can be specified. The optionsl :name is used
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
extra_tags=""
OPTS="`getopt -o d:h:t:f:s:o:p:e: -l database:,extra:,polygon:,subset:,format:,title:,output:,help`"
while test $# -gt 0; do
    case $1 in
        -d|--database) database=$2 ;;
        -s|--subset) subs=$2 ;;
        -f|--format) format=$2 ;;
        -p|--polygon) polys=$2, ;;
        -t|--title) title=$2 ;;
        -o|--output) outfile=$2 ;;
        -e|--extra) extra_tags=$2 ;;
        -h|--help) usage ;;
        --) break ;;
    esac
    shift
done

title="${title:-${database} `echo ${subs} | sed -e 's/:[a-zA-Z0-9]*//'`}"
# Always use a full path
#if test `dirname ${outfile}`; then
#    outfile="$PWD/${outfile}"
#fi

# Process the list of data subsets
declare -a subsets
declare -A subnames
declare -a subtypes
i=1				# array indexes can't start with 0
subs="`echo ${subs} | tr ' ' '_' | tr ',' ' '`"
for sub in ${subs}; do
    subnames[${sub}]="${sub}"
    subsets[$i]="`echo ${sub} | cut -d ':' -f 1`"
    if test "`echo ${supported} | grep -c ${subsets[$i]}`" -eq 0; then
	echo "ERROR: ${sub} not supported!"
	continue
    fi
    # There are two classes of data, waypoints and lines, which are
    # rendered differently.
    case ${subsets[$i]} in
	wifi|lodging|huts|waterfall|swimming) subtypes[$i]="waypoint" ;;
	firewater|helicopter|emergency|camp|addresses) subtypes[$i]="waypoint" ;;
	*) subtypes[${subsets[$i]}]="line" ;;
    esac
    i="`expr $i + 1`"
done

subnames[helicopter]="Landing Zones"
subnames[hike]="Hike/Bike Trails"
subnames[firewater]="Water Sources"
subnames[wifi]="Wifi Access"
subnames[emergency]="Emergency Buildings"
subnames[lodging]="Lodging"
subnames[hut]="Alpine Huts"
subnames[camp]="Campgrounds"
#subnames[camp]="Campsites"
subnames[addresses]="Addresses"
subnames[roads]="Roads"
subnames[trails]="Hiking Trails"
subnames[milestone]="Mile Markers"

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
    outfile="./${database}-${subs}.kml"
fi

rm -f ${outdir}/debug.log

# Our custom Icons for waypoints
icondir=icons
declare -A icons=()
icons[BUILDING]="#Building"
icons[MILESTONE]="#Milestone"
icons[HISTYES]="#Histyes"
icons[ARCHAE]="#Archae"
icons[RUINS]="#Ruins"
icons[BUILDING]="#Building"
icons[AHUT]="#AHut"
icons[HOSTEL]="#Hostel"
icons[HOTEL]="#Hotel"
icons[CASA]="#Casa"
icons[UNKNOWN]="#town"
icons[LODGING]="#Lodging"
icons[WIFI]="#Wifi"
icons[CAMPFIRE]="#Campfire"
icons[CAMPSITE]="#Campsite"
icons[CAMPGROUND]="#Campground"
icons[PICNIC]="#Picnic"
icons[MOUNTAINS]="#Mountains"
icons[HIKER]="#Hiker"
icons[FIRESTATION]="#FireStation"
icons[WATERTANK]="#WaterTowerOutline"
icons[CISTERN]="#Cistern"
icons[FIREPOND]="#FirePond"
icons[HYDRANT]="#Hydrant"
icons[WATER]="#Water"
icons[WATERFALL]="#Waterfall"
icons[SWIMMING]="#Swimming"
icons[LANDINGSITE]="#Helicopter"
icons[HELIPAD]="#Helipad"
icons[HELIPORT]="#Heliport"
icons[PARKING]="#ParkingLot"
icons[TRAILHEAD]="#Trailhead"
icons[PEAK]="#Peak"
icons[BIGPEAK]="#BigPeak"
icons[HOTSPRING]="#HotSpring"

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

# # Make sure the specified polygon is in the database
# if test ${#polygons[@]} -gt 0; then
#     for i in ${!#polygons[@]}; do
# 	echo "Processing ${polynames[$i]}..."
# 	poly_exists ${polygons[$i]}
# 	if test $? -gt 0; then
# 	    echo "ERROR: ${polynames[$i]} doesn't exist in planet_osm_polygon!"
# 	else
# 	    echo "${polynames[$i]} exists in planet_osm_polygon!"
# 	fi
#     done
# fi

# Create the final KML file
kml_file_header ${outfile} "${title}"

tmpout="${outdir}/campgrounds.out"
rm -f ${tmpout}
cat <<EOF >> ${tmpout}
SELECT DISTINCT tags->'is_in' FROM planet_osm_point WHERE tags->'is_in'!='' AND tourism='camp_site';
EOF

kmlstatus="header"
flevel=0
# Execute the query. The index is an integer, whuc can be used in ${subnames} to
# get the full name.
for subset in ${subsets[@]}; do
    # Create the SQL command file
    sqlcmd="`sql_file ${subset} ${outdir}/${database}-${subset}`"
    sqlout="`echo ${sqlcmd} | sed -e 's:\.sql:.tmp:'`"
    kmlout="`echo ${sqlcmd} | sed -e 's:\.sql:.kml:'`"
    fullname="${subnames[${subset}]}"

    # Start the Folder if there is more than one
    if test ${#subsets[@]} -gt 0; then
       kml_folder_start ${kmlout} "${fullname}"
#       kmlstatus="start"
       flevel="`expr ${flevel} + 1`"
    fi

    # execute the query
    psql --tuples-only --dbname=${database} --no-align --file=${sqlcmd} --output=${sqlout}
    index=0
    func="parse_${subset}"

    # print a rotating character, so we know it's working
    rot[0]="|"
    rot[1]="/"
    rot[2]="-"
    rot[3]="\\"
    j=0
    echo ""

    oldname=""
    newname=""
    while read line; do
	# the ISIN field is only set for nodes using the 'is_in' tag to group things
	# like camsites in a campground, or fire hydrants in a city.
	newname="${data[ISIN]}"
	match=`expr "${oldname}" != "${newname}"`
	#echo "FOOBY: ${match} : ${kmlstatus} ${flevel}"
	if test "${flevel}" -gt 1 -a ${match} -eq 1; then
	    kml_folder_end ${kmlout}
#	    kmlstatus="end"
	    flevel="`expr ${flevel} - 1`"
	fi
	if test x"${newname}" != x; then
	    if test ${match} -eq 1; then
	       kml_folder_start ${kmlout} "${newname}"
#	       kmlstatus="start"
	       flevel="`expr ${flevel} + 1`"
	    fi
	    oldname="${newname}" # cache name change
	else
	    oldname=""		# no is_in tag in node
	fi
	id="`echo ${line} | cut -d '|' -f 1`"
	# Bleech, ugly hack to fix errors in strings that screw up parsing.
	name="`echo ${line} | sed -e 's:Rent|::' | cut -d '|' -f 2 | sed -e 's:\&:and:'`"
	way="`echo ${line} | cut -d '|' -f 3`"
	out="`${func} "${line}"`"
	eval $out
	# Some nodes are marked to be ignored, this is primarily used to mark depreciated
	# water sources used for fire response.
	if test x${data[DISUSED]} != x; then
	    echo "WARNING: Dropping ${data[NAME]} as it's disused."
	    continue
	fi
	kml_placemark ${kmlout} "`declare -p data`"
	echo -n -e "\r\t${rot[$j]}"
	if test $j -eq 3; then
	    j=0
	else
	    j=`expr $j + 1`
	fi
    done < ${sqlout}

    while test ${flevel} -gt 0; do
	kml_folder_end ${kmlout}
	flevel="`expr ${flevel} - 1`"
    done
done

cat ${outdir}/*.kml >> ${outfile}
kml_file_footer ${outfile}
kmlstatus="footer"

echo "SQL file is ${sqlcmd}"

# Make a KMZ file if specified
if test x"${format}" = x"kmz"; then
    newout="`basename ${outfile} | sed -e 's:\.kml:.kmz:'`"
    (cd ${topdir} && zip -qrj ${newout} icons)
    echo "Making KMZ file ${newout}"
    zip -q -j ${newout} ${outfile}
    echo "KMZ file is ${newout}"
else
    echo "KML file is ${outfile}"
fi

# cat ${outdir}/*.sql
# rm -fr ${outdir}/*.tmp ${outdir}/*.sql
