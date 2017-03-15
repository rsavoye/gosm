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

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_camp()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`" 
    data[FEE]="`echo ${line} | cut -d '|' -f 4`"
    data[TOILETS]="`echo ${line} | cut -d '|' -f 5`"
    data[WEBSITE]="`echo ${line} | cut -d '|' -f 6`"
    data[OPERATOR]="`echo ${line} | cut -d '|' -f 7`"
    data[SITES]="`echo ${line} | cut -d '|' -f 8`"
    data[AMENITY]="`echo ${line} | cut -d '|' -f 9`"
    data[ICON]='CAMPSITE'

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_historic()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[HISTORIC]="`echo ${line} | cut -d '|' -f 4`"
    case ${data[HISTORIC]} in
	archaeological_site) data[ICON]="ARCHAE";;
	building) data[ICON]="BUILDING";;
	ruins) data[ICON]="RUINS" ;;
	*) data[ICON]='HISTYES' ;;
    esac

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_lodging()
{
#    echo "TRACE: $*"
    
    local line="`echo $1 | sed -e 's:Rent|::'`"
    local tmp=
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2 | sed -e 's:&: and :'`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[TOURISM]="`echo ${line} | cut -d '|' -f 4`"
    tmp="`echo ${line} | cut -d '|' -f 5`"
    if test x"${tmp}" != x; then
	data[PHONE]="`echo ${line} | cut -d '|' -f 5`"
    fi
    tmp="`echo ${line} | cut -d '|' -f 6`"
    if test x"${tmp}" != x; then
	data[EMAIL]="`echo ${line} | cut -d '|' -f 6`"
    fi
    local website="`echo ${line} | cut -d '|' -f 7`"
    if test "`echo ${website} | grep -c '&'`" -eq 0; then
	data[WEBSITE]="`echo ${line} | cut -d '|' -f 7`"
    fi
    tmp="`echo ${line} | cut -d '|' -f 8`"
    if test x"${tmp}" != x; then
	data[STREET]="`echo ${line} | cut -d '|' -f 8`"
    fi
    tmp="`echo ${line} | cut -d '|' -f 9`"
    if test x"${tmp}" != x; then
	data[HOUSENUMBER]="`echo ${line} | cut -d '|' -f 9`"
    fi
    case ${data[TOURISM]} in
	chalet)         data[ICON]="CHALET" ;;
	wilderness_hut) data[ICON]="WHUT" ;;
	alpine_hut)     data[ICON]="AHUT" ;;
	hotel)          data[ICON]="HOTEL" ;;
	hostel)         data[ICON]="HOSTEL" ;;
	*) idx="`echo ${subset} | tr '[:lower:]' '[:upper:]'`" ;;
    esac

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_wifi()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[ICON]="WIFI"

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_waterfall()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[NAMEEN]="`echo ${line} | cut -d '|' -f 4`"
    data[DESCRIPTION]="`echo ${line} | cut -d '|' -f 5`"
    data[ICON]="WATERFALL"

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_trails()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | grep -o "<LineString>.*</LineString>" | sed -e 's:<LineString>::' -e 's:</LineString>::'`"
    data[SAC_SCALE]="`echo ${line} | cut -d '|' -f 4`"
    data[BICYCLE]="`echo ${line} | cut -d '|' -f 5`"
    data[MTB_SCALE]="`echo ${line} | cut -d '|' -f 6`"
    data[ACCESS]="`echo ${line} | cut -d '|' -f 7`"
    data[COLOR]="`trails_color "${data[SAC_SCALE]}" "${data[MTB_SCALE]}" "${data[ACCESS]}"`"

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_piste()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    # Remove the LineString, which gets put back later when generating the KML.
    # That is because extra elemetns are added.
    data[WAY]="`echo ${line} | grep -o "<LineString>.*</LineString>" | sed -e 's:<LineString>::' -e 's:</LineString>::'`"
    data[PISTE_TYPE]="`echo ${line} | cut -d '|' -f 4`"
    data[PISTE_DIFFICULTY]="`echo ${line} | cut -d '|' -f 5`"
    data[PISTE_GROOMING]="`echo ${line} | cut -d '|' -f 6`"
    data[AERIALWAY]="`echo ${line} | cut -d '|' -f 7`"
    data[ACCESS]="`echo ${line} | cut -d '|' -f 8`"
    data[COLOR]="`ski_color "${data[PISTE_TYPE]}" "${data[PISTE_DIFFICULTY]}" "${data[PISTE_GROOMING]}" "${data[AERIALWAY]}" "${data[ACCESS]}"`"

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_roads()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${linestring:12} | cut -d '<' -f 1-3`"
#    data[COLOR]="`roads_color "${piste_type}" "${piste_difficulty}" "${piste_grooming}" "${aerialway}" "${access}"`"

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_emergency()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    local amenity="`echo ${line} | cut -d '|' -f 4`"
    local emergency="`echo ${line} | cut -d '|' -f 5`"
    local type"`echo ${line} | cut -d '|' -f 6`"
    local diameter="`echo ${line} | cut -d '|' -f 7`"

    case "${amenity}" in
	fire_station) data[ICON]="FIRESTATION" ;;
	fire_hydrant)
	    case "${type}" in
		underground) data[ICON]="CISTERN" ;;
		pond) data[ICON]="WATER" ;;
#	        pillar) data[ICON]="PILLAR" ;;
#	        wall) data[ICON]="WALL" ;;
		*) data[ICON]="HYDRANT" ;;
	    esac
	    ;;
	water_tank) data[ICON]="CISTERN" ;;
	*) ;;
    esac

    echo `declare -p data`
    return 0
}

