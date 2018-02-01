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

# KML Color chart from http://www.zonums.com/gmaps/kml_color
declare -A colors=()
opacity="ff"
# Primary
colors[WHITE]="${opacity}ffffff"
colors[GRAY]="${opacity}888888"
colors[BLACK]="${opacity}000000"
colors[YELLOW]="${opacity}00ffff"
colors[ORANGE]="${opacity}00a5ff"
# Reds
colors[RED]="${opacity}0000ff"
colors[PINK]="${opacity}f00078"
colors[MAGENTA]="${opacity}ff00ff"
colors[PURPLE]="${opacity}800080"
# Blues
colors[CYAN]="${opacity}ffff00"
colors[LIGHTBLUE]="${opacity}e6d8ad"
colors[DARKBLUE]="${opacity}a00000"
colors[BLUE]="${opacity}ff0000"
# Greens
colors[LIGHTGREEN]="${opacity}90ee90"
colors[GREEN]="${opacity}00ff00"
colors[DARKGREEN]="${opacity}006400"
# Browns
colors[BROWN]="${opacity}ff0055aa"

# smoothness=excellent roller blade/skate board and all below
# smoothness=good racing bike and all below
# smoothness=intermediate city bike/sport cars/wheel chair/Scooter and all below
# smoothness=bad trekking bike/normal cars/Rickshaw and all below
# smoothness=very_bad Car with high clearance/ Mountain bike without crampons and all below
# smoothness=horrible 4wd and all below
# smoothness=very_horrible tractor/ATV/tanks/trial/Mountain bike
# smoothness=impassable no wheeled vehicles 

# Road styles are complicacted, as the final result is a mix of the highway type,
# the smoothness, the surface, and the tracktype. Since our goal is oriented
# towards emergency response, our main criteria is what type f apparatus to
# respond in, ie... fire truck, pickup, or UTV. As not all tags exist for all
# data, they're ranked by most likely to least likely to exist, but if they exist,
# they should replace any existing value.
# $1 - The Highway type
# $2 - The surface type
# $3 - Access
roads_color()
{
    local highway="$1"
    local surface="$2"
    local access="$3"
    local smoothness="$4"
    local tracktype="$5"
    local jeep="$6"
    local color="GRAY"

    # http://wiki.openstreetmap.org/wiki/Map_Features#Highway
    # motorway - pink
    # trunk - darker orange
    # primary - light orange
    # secondry - yellow
    # For highway surface types
    case ${highway} in
	tertiary|service|gravel) # (like Upper Moon)
	    color="LIGHTBLUE"
	    ;;
	unclassified) # (like Rollins Pass)
	    color="PINK"
	    ;;
	road|residential|secondary|primary|trunk|motorway_link|trunk_link|secondary_link|teriary_link)
	    color="LIGHTGREEN"
	    ;;
	# Track colors usually get changed based on the surface type.
	track)
	    color="BROWN"
	    ;;
	*)
#	    echo "WARNING: unknown highway surface"
	    ;;
    esac

    # These road surfaces are potentially bad, flag them
    case ${surface} in
	#unpaved|dirt|earth|grass|*gravel*|mud|ice|ground|unpaved) color="ORANGE" ;;
#	unpaved|asphalt|concrete|dirt|earth|grass|gravel_turf|fine_gravel|gravel|mud|ice) color="ORANGE" ;;
	*) ;;
    esac

    case ${access} in
	private|no|forestry|discouraged) color="PINK" ;;
#	public|yes|permissive) color="" ;;
	*) ;;
    esac

    case ${jeep} in
	yes) color=ORANGE ;;
	no) ;;
	*) ;;
    esac

    case ${smoothness} in
	# roller blade/skate board and all below
	excellent) color="GREEN" ;;
	# racing bike and all below
	good) color="GREEN" ;;
	# city bike/sport cars/wheel chair/Scooter and all below
	intermediate) color="DARKGREEN" ;;
	# trekking bike/normal cars/Rickshaw and all below
	bad) color="DARKGREEN" ;;
	# Car with high clearance vehicle or Mountain bike
	# below
	very_bad) color="ORANGE" ;;
	# 4wd and all below
	horrible) color="ORANGE" ;;
	# tractor/ATV/tanks/trial/Mountain bike
	very_horrible) color="PURPLE" ;;
	# no wheeled vehicles 
	impassable) color="BLACK" ;;
	*) ;;
    esac

    case ${tracktype} in
	grade1) ;; # Solid, paved or compacted
	grade2) ;; # Mostly Solid, unpaved, mix of sand, silt, and clay
	grade3) ;; # Mix of hard and soft materials
	grade4) ;; # Unpaved, lacks hard material, might be grass
	grade5) ;; # 
	*) ;;
    esac
    echo ${color}

    return 0
}

# http://wiki.openstreetmap.org/wiki/Piste_Maps#Type
# OSM colors used are green, blue, red, black, orange, yellow
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
	    echo "DARKGREEN"
	    return 0
	    ;;
	chair_lift)
	    echo "MAGENTA"
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
# Tag SAC Scale (as seen on ground signs) Alpine Paper Maps (Austria)
# sac_scale=hiking T1 yellow solid red
# sac_scale=mountain_hiking T2 red dashed red
# sac_scale=demanding_mountain_hiking T3 red dashed red
# sac_scale=alpine_hiking T4 blue dotted red
# sac_scale=demanding_alpine_hiking T5 blue dotted red
# sac_scale=difficult_alpine_hiking T6 blue dotted red 
trails_color()
{
    if test x"${debug}" = x"yes"; then
	echo "trail_color ($*)" >> /tmp/debug.log
    fi

    local sac_scale="$1"
    local mtb_scale_imba="$2"
    local access="$3"

    local color="BLUE"	# default color

    # http://wiki.openstreetmap.org/wiki/Key:sac_scale
    # hiking = Trail well cleared
    # mountain_hiking - Trail with continuous line and balanced ascent
    # demanding_mountain_hiking - exposed sites may be secured with ropes or chains,
    #                             possible need to use hands for balance
    # Mountain hiking scale
    if test x"${sac_scale}" != x; then
	case ${sac_scale} in
	    hiking) color="YELLOW" ;;
	    mountain_hiking|demanding_mountain_hiking) color="PINK" ;;
	    alpine_hiking|difficult_alpine_hiking|demanding_alpine_hiking) color="MAGENTA" ;;
	    *) ;;
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
	    1*) color="LIGHTGREEN" ;;  # easy
	    2*) color="LIGHTBLUE" ;;   # intermediate
	    3*) color="GRAY" ;;  # difficult
	    4*) color="BLACK" ;; # double black
	    *)  ;;
	esac
    fi
    # http://wiki.openstreetmap.org/wiki/Key:mtb:scale
    if test x"${mtb_scale}" != x  -a x"${sac_scale}" = x; then
	case ${mtb_scale} in # 0-6
	    0*) color="YELLOW" ;;
	    1*) color="LIGHTGREEN" ;;
	    2*) color="LIGHTGREEN" ;;
	    3*) color="LIGHTBLUE" ;;
	    4*) color="LIGHTBLUE" ;;
	    5*) color="MAGENTA" ;;
	    6*) color="BLACK" ;;
	    *)  ;;
	esac
    fi
    
    echo "${color}"
    return 0
}
