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

# $1 - The SAC scale
# $2 - The MTB scale
# $3 - The access. ie... don't go here if not allowed
trails_color()
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
