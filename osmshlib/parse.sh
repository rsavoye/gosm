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
parse_trailhead()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`" 
    if test `echo ${data[WAY]} | grep -c Polygon` -eq 0; then
	data[ICON]='TRAILHEAD'
    else
	data[WAY]="`echo ${data[WAY]} | sed -e 's:<Polygon>::' -e 's:</Polygon>::'`" 
	data[FILL]='PURPLE'
    fi

    echo `declare -p data`
    return 0
}

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
    data[LEISURE]="`echo ${line} | cut -d '|' -f 10`"
    data[TOURISM]="`echo ${line} | cut -d '|' -f 11`"

    if test x"${data[LEISURE]}" = x'firepit'; then
	data[ICON]='CAMPFIRE'
    fi
    if test x"${data[TOURISM]}" = x'camp_site'; then
	data[ICON]='CAMPSITE'
    fi
    if test x"${data[AMENITY]}" = x'campground'; then
	data[ICON]='CAMPGROUND'
    fi

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_milestone()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`" 
    data[ALTNAME]="`echo ${line} | cut -d '|' -f 4`"
    data[ICON]='MILESTONE'

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_helicopter()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`" 
    data[EMERGENCY]="`echo ${line} | cut -d '|' -f 4`"
    data[AEROWAY]="`echo ${line} | cut -d '|' -f 5`"
    data[ICON]='LANDINGSITE'

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
    tmp="`echo ${line} | cut -d '|' -f 10`"
    if test x"${tmp}" != x; then
	data[NAMEEN]="`echo ${line} | cut -d '|' -f 10`"
    fi
    case ${data[TOURISM]} in
	chalet)         data[ICON]="CHALET" ;;
	wilderness_hut) data[ICON]="WHUT" ;;
	alpine_hut)     data[ICON]="AHUT" ;;
	hotel)          data[ICON]="HOTEL" ;;
	hostel)         data[ICON]="HOSTEL" ;;
	camp_site)      data[ICON]="CAMPSITE" ;;
	campground)     data[ICON]="CAMPGROUND" ;;
	hot_spring)     data[ICON]="HOTSPRING" ;;
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
parse_peak()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[ELEVATION]="`echo ${line} | cut -d '|' -f 4`"
    data[ICON]="PEAK"

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_hotspring()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[ICON]="HOTSPRING"

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
    data[NAME]="`echo ${line} | cut -d '|' -f 4`"
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

    local width="2"
    data[WIDTH]="${width}"

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
    data[WAY]="`echo ${line} | grep -o "<LineString>.*</LineString>" | sed -e 's:<LineString>::' -e 's:</LineString>::'`"
    data[HIGHWAY]="`echo ${line} | cut -d '|' -f 4`"
    data[SURFACE]="`echo ${line} | cut -d '|' -f 5`"
    data[ACCESS]="`echo ${line} | cut -d '|' -f 6`"
    data[SMOOTHNESS]="`echo ${line} | cut -d '|' -f 7`"
    data[TRACETYPE]="`echo ${line} | cut -d '|' -f 8`"
    data[ALTNAME]="`echo ${line} | cut -d '|' -f 9`"
    data[4WD]="`echo ${line} | cut -d '|' -f 10`"
    data[COLOR]="`roads_color "${data[HIGHWAY]}" "${data[SURFACE]}" "${data[ACCESS]}" "${data[SMOOTHNESS]}" "${data[TRACKTYPE]}"`"

    local width=5
    case $data[SMOOTHNESS] in
	excellent) ;; # roller blade/skate board and all below
	good) ;; # racing bike and all below
	intermediate) ;; # city bike/sport cars/wheel chair/Scooter and all below
	bad) width=4 ;; # trekking bike/normal cars/Rickshaw and all below
	very_bad) ;; # Car with high clearance/ Mountain bike without crampons and all below
	horrible) width=3;; # 4wd and all below
	very_horrible) ;; # tractor/ATV/tanks/trial/Mountain bike
	impassable) ;; #no wheeled vehicles 
	*) ;;
    esac

    case $data[TRACKTYPE] in
	grade1) ;; # Solid, paved or compacted
	grade2) ;; # Mostly Solid, unpaved, mix of sand, silt, and clay
	grade3) width=3 ;; # Mix of hard and soft materials
	grade4) ;; # Unpaved, lacks hard material, might be grass
	grade5) ;; # 
	*) ;;
    esac
    data[WIDTH]="${width}"

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
    data[AMENITY]="`echo ${line} | cut -d '|' -f 4`"
    data[EMERGENCY]="`echo ${line} | cut -d '|' -f 5`"

    case "${data[AMENITY]}" in
	fire_station) data[ICON]="FIRESTATION" ;;
	police) data[ICON]="POLICE" ;;
	hospital) data[ICON]="HOSPITAL" ;;
    esac

    case "${data[EMERGENCY]}" in
	fire_hydrant) data[ICON]="HYDRANT" ;;
	landing_site) data[ICON]="LANDINGSITE" ;;
	water_tank) data[ICON]="CISTERN" ;;
	suction_point) data[ICON]="FIREPOND" ;;
	fire_water_pond) data[ICON]="FIREPOND" ;;
	*) ;;
    esac

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_firewater()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[EMERGENCY]="`echo ${line} | cut -d '|' -f 4`"
    data[HYDRANTTYPE]="`echo ${line} | cut -d '|' -f 5`"
    data[HYDRANTDIA]="`echo ${line} | cut -d '|' -f 6`"
    data[WATER]="`echo ${line} | cut -d '|' -f 7`"
    data[VOLUMNE]="`echo ${line} | cut -d '|' -f 8`"
    data[NOTE]="`echo ${line} | cut -d '|' -f 9`"
    data[DISUSED]="`echo ${line} | cut -d '|' -f 10`"

    case "${data[HYDRANTTYPE]}" in
	underground) data[ICON]="CISTERN" ;;
	pond) data[ICON]="WATER" ;;
	pillar) data[ICON]="PILLAR" ;;
	wall) data[ICON]="WALL" ;;
	*) data[ICON]="HYDRANT" ;;
    esac

    case "${data[WATER]}" in
	landing_site) data[ICON]="WATER" ;;
	*) ;;
    esac

    case "${data[EMERGENCY]}" in
	fire_hydrant) data[ICON]="HYDRANT" ;;
	landing_site) data[ICON]="LANDINGSITE" ;;
	water_tank) data[ICON]="CISTERN" ;;
	suction_point) data[ICON]="FIREPOND" ;;
	fire_water_pond) data[ICON]="FIREPOND" ;;
	*) ;;
    esac

    echo `declare -p data`
    return 0
}

# Parse a line that is the output of the SQL query
# $1 - A line of text from the SQL query output
parse_helicopter()
{
#    echo "TRACE: $*"

    local line="$1"
    declare -A data=()

    data[OSMID]="`echo ${line} | cut -d '|' -f 1`"
    data[NAME]="`echo ${line} | cut -d '|' -f 2`"
    data[WAY]="`echo ${line} | cut -d '|' -f 3`"
    data[EMERGENCY]="`echo ${line} | cut -d '|' -f 4`"
    data[AEROWAY]="`echo ${line} | cut -d '|' -f 5`"

    case "${data[EMERGENCY]}" in
	fire_hydrant) data[ICON]="HYDRANT" ;;
	landing_site) data[ICON]="LANDINGSITE" ;;
	water_tank) data[ICON]="CISTERN" ;;
	suction_point) data[ICON]="FIREPOND" ;;
	fire_water_pond) data[ICON]="FIREPOND" ;;
	*) ;;
    esac

    case "${data[AEROWAY]}" in
	heliport) data[ICON]="HELIPORT" ;;
	helipad) data[ICON]="HELIPAD" ;;
	*) ;;
    esac

    echo `declare -p data`
    return 0
}
