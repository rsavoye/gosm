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

# Create the KML file header
# $1 - name of the output file
# $2 - Title in the file
kml_file_header ()
{
    local outfile="$1"
    local title="$2"
    
    cat <<EOF > ${outfile}
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2">
<Document>
    <name>${title}</name>
    <visibility>1</visibility>
    <open>1</open>
EOF
    
    cat ${topdir}/styles.kml >> ${outfile}

    return 0
}

# Append the KML file footer
# $1 - name of the output file
kml_file_footer ()
{
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
    local outfile="$1"
    local folder="$2"

    echo -n -e "\rStarting folder: ${folder}"
    
    cat <<EOF > ${outfile}
    <Folder>
        <name>${folder}</name>
EOF
    
    return 0
}

# Create a Folder entry inth KML file
# $1 - name of the output file
kml_folder_end ()
{
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
#    echo "TRACE: $*"
    
    local outfile="$1"
    eval "$2"
    local name="`echo ${data[NAME]} | sed -e 's:&: and :'`"

    if test x"${data[WAY]}" = x; then
	echo "WARNING: Way has no coordinates! ${name}"
	return 1
    fi

#    declare -p data
    cat <<EOF >> ${outfile}
        <Placemark>
            <name>${name:-"OSM-ID ${data[OSMID]}"}</name>
EOF
    if test x"${data[ICON]}" != x; then
	icon="${icons[${data[ICON]}]}"
#	echo "icon = ${data[ICON]} ${icons[${data[ICON]}]}"
	cat <<EOF >> ${outfile}
            <styleUrl>${icon}</styleUrl>
EOF
    fi
    if test x"${data[COLOR]}" != x; then
	style="`echo ${data[COLOR]} | tr '[:upper:]' '[:lower:]'`"
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
    if test x"${data[FILL]}" != x; then
	cat <<EOF >> ${outfile}
            <styleUrl>#Polygon</styleUrl>
EOF
    fi

    # Create the description popup box
    if test ${#data[@]} -gt 3; then
 	echo "<description>"  >> ${outfile} 	
	for i in ${!data[@]}; do
	    case $i in
		# ignore these, they're not part of the descriptiom
		WIDTH|FILL|NAME|WAY|ICON|TOURISM|AMENITY|WATERWAY|HIGHWAY|EMERGENCY|COLOR|MILESTONE) ;;
		*)
		    if test x"${data[$i]}" != x; then
			local cap="${i:0:1}"
			local rest="`echo ${i:1:${#i}} | tr '[:upper:]' '[:lower:]'`"
 			echo "${cap}${rest}: `echo ${data[$i]} | sed -e 's:&: and :'`"  >> ${outfile}
		    fi
		    ;;
	    esac
	done
 	echo "</description>"  >> ${outfile}
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
            <extrude>1</extrude>
            <altitudeMode>relativeToGround</altitudeMode>
             ${data[WAY]}
        </Polygon>
EOF
    fi
    cat <<EOF >> ${outfile}
        </Placemark>
EOF

    return 0
}
