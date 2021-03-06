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

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have tags signifying what type
# it is.

osmbin="`which $0`"
topdir="`dirname ${osmbin}`"
. "${topdir}/osmshlib/colors.sh" || exit 1
. "${topdir}/osmshlib/styles.sh" || exit 1

# Create the KML file header
# $1 - name of the output file
# $2 - Title in the file
kml_file_header ()
{
#    echo "TRACE: kml_file_header()"

    local outfile="${1}"
    local title="${2}"
    local args="${3}"
    
    cat <<EOF > ${outfile}
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2">
<Document>
    <name>${title}</name>
    <visibility>1</visibility>
    <open>1</open>
EOF
    # linecolors="lightblue yellow lightgreen pink orange red green"
    # for style in ${args}; do
    # 	# lines obviously don't have an icon
    # 	if test x"${style}" = x'roads' -o x"${style}" = x'trails' -o x"${style}" = x'piste'; then
    # 	    for color in ${linecolors}; do
    # 		cat ${topdir}/styles/${color}line.kml >> ${outfile}
    # 	    done
    # 	    continue
    # 	else			# some subsets have multiple possible icons
    # 	    case ${style} in
    # 		addresses*)
    # 		    cat ${topdir}/styles/camp*.kml >> ${outfile}
    # 		    ;;
    # 		camp*)
    # 		    cat ${topdir}/styles/camp*.kml >> ${outfile}
    # 		    ;;
    # 		historic*)
    # 		    cat ${topdir}/styles/ruins.kml >> ${outfile}
    # 		    cat ${topdir}/styles/archae.kml >> ${outfile}
    # 		    ;;
    # 		lodging*)
    # 		    cat ${topdir}/styles/hostel.kml >> ${outfile}
    # 		    cat ${topdir}/styles/hotel.kml >> ${outfile}
    # 		    cat ${topdir}/styles/lodging.kml >> ${outfile}
    # 		    ;;
    # 		fire*)
    # 		    cat ${topdir}/styles/firepond.kml >> ${outfile}
    # 		    cat ${topdir}/styles/hydrant.kml >> ${outfile}
    # 		    cat ${topdir}/styles/cistern.kml >> ${outfile}
    # 		    ;;
    # 		*)		# helicopter, waterfall, swimming
    # 		    cat ${topdir}/styles/${style}.kml >> ${outfile}
    # 		    ;;
    # 	    esac
    # 	fi
    # done
    cat ${topdir}/styles.kml >> ${outfile}

    return 0
}

# Append the KML file footer
# $1 - name of the output file
kml_file_footer ()
{
#    echo "TRACE: $*"

    local outfile="$1"
    
    cat <<EOF >> ${outfile}
</Document>
</kml>
EOF

    return 0
}

# Create a Folder entry inth KML file
# $1 - name of the output file
# $2 - name of the Folder
kml_folder_start ()
{
#    echo "TRACE: kml_folder_start($2)"

    local outfile="$1"
    local folder="$2"

    echo ""
    echo -n -e "\rStarting folder: ${folder}"
    
    cat <<EOF >> ${outfile}
    <Folder>
        <name>${folder}</name>
EOF

    return 0
}

# Create a Folder entry inth KML file
# $1 - name of the output file
kml_folder_end ()
{
#    echo "TRACE: kml_folder_end()"

    local outfile="$1"

    #    echo ""
    cat <<EOF >> ${outfile}
    </Folder>
EOF
    
    return 0
}

# Create a Placemark entry in the KML file
# $1 - name of the output file
# $2 - coordinates
# $2 - description array
kml_placemark ()
{
#    echo "	TRACE: kml_placemark(${data[NAME]})"
    
    local outfile="$1"
    eval "$2"
    local name="`echo ${data[NAME]} | sed -e 's:&: and :'`"
    if test x"${name}" = x; then
	local name="`echo ${data[NAMEEN]} | sed -e 's:&: and :'`"
    fi

    if test x"${data[WAY]}" = x; then
	echo "WARNING: Way has no coordinates! ${name}"
	return 1
    fi

    #    declare -p data
    echo "        <Placemark>"  >> ${outfile}
    if test x"${name}" != x; then
	cat <<EOF >> ${outfile}
            <name>${name}</name>
EOF
	#      <name>${name:-"OSM-ID ${data[OSMID]}"}</name>
    fi
    if test x"${data[ICON]}" != x; then
	icon="${icons[${data[ICON]}]}"
#	echo "icon = ${data[ICON]} ${icons[${data[ICON]}]}"
	cat <<EOF >> ${outfile}
            <styleUrl>${icon}</styleUrl>
EOF
    fi
    if test x"${data[COLOR]}" != x; then
	style="`echo ${data[COLOR]} | tr '[:upper:]' '[:lower:]'`"
# 	cat <<EOF >> ${outfile}
#             <color>${colors[${data[COLOR]}]}</color>
# EOF
	cat <<EOF >> ${outfile}
            <styleUrl>#line_${style}</styleUrl>
EOF
    # Only lines have the WIDTH set
    if test x"${data[WIDTH]}" != x; then
	cat <<EOF >> ${outfile}
            <width>${data[WIDTH]}</width>
EOF
    fi

    fi

    case "${data[FILL]}" in
	"red")
	    echo "<styleUrl>#PolygonRed</styleUrl>" >> ${outfile}
	    ;;
	"green")
	    echo "<styleUrl>#PolygonGreen</styleUrl>" >> ${outfile}
	    ;;
	"yellow")
	    echo "<styleUrl>#PolygonYellow</styleUrl>" >> ${outfile}
	    ;;
	"purple")
	    echo "<styleUrl>#PolygonPurple</styleUrl>" >> ${outfile}
	    ;;
	"blue")
	    echo "<styleUrl>#PolygonBlue</styleUrl>" >> ${outfile}
	    ;;
    esac

    # echo "FIXME: $outfile"
    # Create the description popup box
    if test ${#data[@]} -gt 3; then
	echo "<description>"  >> ${outfile}
	for i in ${!data[@]}; do
	    case $i in
		# ignore these, they're not part of the descriptiom
		WIDTH|FILL|FULL|WAY|ICON|TOURISM|AMENITY|WATERWAY|HIGHWAY|EMERGENCY|COLOR|MILESTONE|STREET|NUMBER|BOUNDARY|ADMIN_LEVEL|NAME|NAMEEN)
		;;
		ALT_NAME)
		    # Since both field may exist, only set the name once.
		    #echo "FIXME1: \"${data[NAME]}\""
		    #echo "FIXME2: \"${data[ALT_NAME]}\""
		    # if the name is an OSM ID, check the alt_name field
		    # 	if test "`echo ${data[NAME]} | grep -c '^-[0-9]*'`" -gt 0; then
		    # 	    if test x"${data[ALT_NAME]}" != x; then
		    # 		echo "${data[ALT_NAME]}" >> ${outfile}
		    # 	    else
		    # 		echo "Unknown" >> ${outfile}
		    # 	    fi
		    # 	    hit=true
		    # 	    continue
		    # 	fi
		    # else
		    # 	hit=false
		    # fi
		    if test x"${data[NAME]}" = x -a x"${data[ALT_NAME]}" != x; then
			echo "${data[ALT_NAME]}" >> ${outfile}
			continue
		    elif test x"${data[NAME]}" != x -a x"${data[ALT_NAME]}" != x; then
			echo "Parcel ID: ${data[ALT_NAME]}" >> ${outfile}
			continue
		    fi
		;;
		ADDRFULL)
		    echo "${data[ADDRFULL]}" >> ${outfile}
		;;
		ISIN)
		    if test x"${data[ISIN]}" != x; then
			echo "Is In: ${data[ISIN]}" >> ${outfile}
		    fi
		;;
		DESCRIPTION)
		    echo "${data[DESCRIPTION]}" >> ${outfile}
		;;
		OSMID)
		    if test x$"{data[NUMBER]" = x; then
			echo "Osmid: ${data[OSMID]}" >> ${outfile}
		    fi
		;;
		*)
		    if test x"${data[$i]}" != x; then
			local cap="${i:0:1}"
			local rest="`echo ${i:1:${#i}} | tr '[:upper:]' '[:lower:]'`"
 			echo "${cap}${rest}: `echo ${data[$i]} | sed -e 's:&: and :'`"  >> ${outfile}
		    fi
		    ;;
	    esac
	done
	if test x"${name}" = x; then
	    echo "OSM-ID ${data[OSMID]}" >> ${outfile}
	fi
 	echo "</description>" >> ${outfile}
    fi

    # Only lines have COLOR set
    if test x"${data[COLOR]}" != x; then
	cat <<EOF >> ${outfile}
        <LineString>
            <tessellate>1</tessellate>
            <altitudeMode>clampToGround</altitudeMode>
           ${data[WAY]}
        </LineString>
EOF
    fi

    # Only waypoints have ICON set
    if test x"${data[ICON]}" != x; then
	cat <<EOF >> ${outfile}
           ${data[WAY]}
EOF
    fi

    # Only Polygons have FILL set
    if test x"${data[FILL]}" != x; then
	cat <<EOF >> ${outfile}
        <Polygon>
            <outerBoundaryIs>
               <LinearRing>
                <altitudeMode>relativeToGround</altitudeMode>
                ${data[WAY]}
              </LinearRing>
	    </outerBoundaryIs>
        </Polygon>
EOF
    fi
    cat <<EOF >> ${outfile}
        </Placemark>
EOF

    return 0
}
