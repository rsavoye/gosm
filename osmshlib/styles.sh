# 
# Copyright (C) 2016, 2017, 2018, 2019, 2020   Free Software Foundation, Inc.
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
icons[GUEST]="#Guest"
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
icons[PLACE]="#Place"
icons[TOWN]="#Town "

# Our custom Styles for waypoints
icondir=styles
declare -A styles=()
styles[BUILDING]=.kml"styles/building.kml.kml"
styles[MILESTONE]=.kml"styles/milestone.kml"
styles[HISTYES]=.kml"styles/histyes.kml"
styles[ARCHAE]=.kml"styles/archae.kml"
styles[RUINS]=.kml"styles/ruins.kml"
styles[AHUT]=.kml"styles/ahut.kml"
styles[GUEST]=.kml"styles/guesthouse.kml"
styles[HOSTEL]=.kml"styles/hostel.kml"
styles[HOTEL]=.kml"styles/hotel.kml"
styles[CASA]=.kml"styles/casa.kml"
styles[UNKNOWN]=.kml"styles/town.kml"
styles[LODGING]=.kml"styles/lodging.kml"
styles[WIFI]=.kml"styles/wifi.kml"
styles[CAMPFIRE]=.kml"styles/campfire.kml"
styles[CAMPSITE]=.kml"styles/campsite.kml"
styles[CAMPGROUND]=.kml"styles/campground.kml"
styles[PICNIC]=.kml"styles/picnic.kml"
styles[MOUNTAINS]=.kml"styles/mountains.kml"
styles[HIKER]=.kml"styles/hiker.kml"
styles[FIRESTATION]=.kml"styles/firestation.kml"
styles[WATERTANK]=.kml"styles/watertoweroutline.kml"
styles[CISTERN]=.kml"styles/cistern.kml"
styles[FIREPOND]=.kml"styles/firepond.kml"
styles[HYDRANT]=.kml"styles/hydrant.kml"
styles[WATER]=.kml"styles/water.kml"
styles[WATERFALL]=.kml"styles/waterfall.kml"
styles[SWIMMING]=.kml"styles/swimming.kml"
styles[LANDINGSITE]=.kml"styles/helicopter.kml"
styles[HELIPAD]=.kml"styles/helipad.kml"
styles[HELIPORT]=.kml"styles/heliport.kml"
styles[PARKING]=.kml"styles/parkingLot.kml"
styles[TRAILHEAD]=.kml"styles/trailhead.kml"
styles[PEAK]=.kml"styles/peak.kml"
styles[BIGPEAK]=.kml"styles/bigpeak.kml"
styles[HOTSPRING]=.kml"styles/hotspring.kml"
styles[PLACE]=.kml"styles/place.kml"
styles[TOWN]=.kml"styles/town.kml"

get_style()
{
    local tag="${1:-UNKNOWN}"
    local scale="${2:-1.0}"
}

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

