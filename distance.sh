#!/bin/bash

#
# This is a truly ugly script, but it's single purpose. This calculates the
# driving time and distance in miles from a water source or fire station to
# an incident address. We need this for ISO certification for my fire department.
#

apikey="AIzaSyCmJWynjNtcpoAY8i_6nsEbmNiox8WlZDg"
url="https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=711 Eureka Street, Black Hawk, CO&destinations=New+York+City,NY&key=AIzaSyCmJWynjNtcpoAY8i_6nsEbmNiox8WlZDg"
otype="xml"			# Can also be json

# These are the response address to use as the destination.
#senarios[0]="711 Eureka Street, Black Hawk, CO"
#senarios[0]="1152 Upper Apex Valley Road, Black Hawk, CO"
senarios[0]="1155 Bald Mountain Road,  Black Hawk, CO"
#senarios[1]="12 Dill Pickle Place, Black Hawk, CO"
senarios[1]="95 Paradise Valley Parkway, Black Hawk, CO"
senarios[2]="286 Norton Drive, Black Hawk, CO"
senarios[3]="30 Trail Dust Road, Black Hawk, CO"
senarios[4]="460 Beethoven Drive, Black Hawk, CO"
senarios[5]="15107 Highway 119, CO"
senarios[6]="19 Old Stagecoach Trail, Rollinsville, CO"
#senarios[7]="6115 Magnolia Road, Boulder, CO"
senarios[7]="28 Frontier Lane, Boulder, CO"
senarios[8]="5015 Magnolia Drive, Boulder, CO"
senarios[9]="375 County Road 68, Boulder, CO"
senarios[10]="233 Deer Circle, Black Hawk, CO"
senarios[11]=""			# Terminator

# GPS coordinates of water sources. We uses coordinate as not all water
# sources, like cisterns, have an address.
sources[0]="39.80445,-105.52895"		# Hydrant 50
sources[1]="39.83314,-105.52966"		# Rec Center Hydrant
sources[2]="39.83970,-105.48030"		# Paradise Valley
sources[3]="39.86836,-105.46672"		# Ameristar
sources[4]="39.83250,-105.43304"		# Eagle Rock
# Timberline Stations
sources[5]="39.97666,-105.41722"		# Station 1 Cistern
sources[6]="39.9174817,-105.5054733"		# Station 3
sources[7]="39.892013,-105.4815131"		# Station 4
sources[8]="39.8645572,-105.4658424"		# Station 5
sources[9]="39.8398505,-105.4815195"		# Station 7
sources[10]="39.82104,-105.40708"		# Station 8
# Nederland Stations
sources[11]="39.9638041,-105.5163478"	# Station 1, highway 119
sources[12]="39.9813625,-105.4643161"	# Station 2, Ridge Road
#sources[13]="39.9493937,-105.5694146"	# Station 3, Eldora
# Coal Creek Stations
sources[13]="39.9062905,-105.3475074"	# Station 1, Coal Creek Road
sources[14]="39.8764173,-105.3942718"	# Station 4, Gap Road
# Golden Gate Stations
sources[15]="39.7769625,-105.3681796" # Station 1, Robinson Hill
sources[16]="39.8253467,-105.3116775" # Station 2, Crawford Gulch Road
# Sugarloaf Stations
sources[17]="40.0168869,-105.3578494" # Station 1
sources[18]="40.019052,-105.4048271"  # Station 2
sources[19]="40.0042491,-105.4648197" # Station 3
# EOF
sources[20]=""					# Terminator

# Names for the water source coordinates
names[0]="Hydrant 50"
names[1]="Paradise Valley Cistern"
names[2]="Rec Center Hydrant"
names[3]="Ameristar Warehouse"
names[4]="Eagle Rock Cistern"
names[5]="Timberline Station 1"
names[6]="Timberline Station 3"
names[7]="Timberline Station 4"
names[8]="Timberline Station 5"
names[9]="Timberline Station 7"
names[10]="Timberline Station 8"
names[11]="Nederland Station 1"
names[12]="Nederland Station 2"
names[13]="Coal Creek Station 1"
names[14]="Coal Creek Station 2"
names[15]="Golden Gate Station 1"
names[16]="Golden Gate Station 2"
names[17]="Sugar Loaf Station 1"
names[18]="Sugar Loaf Station 2"
names[19]="Sugar Loaf Station 3"
names[20]=""

storage[0]="city water"
storage[1]="city water"
storage[2]="300,000"
storage[3]="100,000"
storage[4]="60,000"
storage[5]="35,000"
storage[6]=""
storage[7]=""
storage[8]=""
storage[9]=""
storage[10]=""
storage[11]=""
storage[12]=""
storage[13]=""
storage[14]=""
storage[15]=""
storage[16]=""
storage[17]=""
storage[18]=""

csv="/tmp/distance.csv"
# Create output file
echo "Address,WaterSource,Minutes,Miles" > ${csv}

i=-1
while test "${senarios[$i]}" != x} ; do
    i="`expr $i + 1`"
    origin="${senarios[$i]}"
    start="`echo ${origin} | cut -d ',' -f 1`"
    j=0
    while test "${sources[$j]}" != x; do
	dest="${sources[$j]}"
	echo "Processing ${origin} to ${dest}..."
	end="`echo ${dest} | tr -d ','`"
	# end="`echo ${dest} | cut -d ',' -f 1`"
	tmpfile="`echo /tmp/distance.${start}-${end} | tr -d ' '`"
	if test ! -e ${tmpfile}; then
	    lynx -dump "https://maps.googleapis.com/maps/api/distancematrix/${otype}?units=imperial&origins=${origin}&destinations=${dest}&key=${apikey}" >& "${tmpfile}"
	fi
	out="`grep "text" ${tmpfile}`"
	#minutes="`echo ${out} | grep -o "[0-9\.]* min<" | tr -d '<' | cut -d ' ' -f 1`"
	minutes="`echo ${out} | grep -o "[0-9\.]* min.*<" | tr -d '<' | cut -d ' ' -f 1`"
	miles="`echo ${out} | grep -o "[0-9\.]* mi<" | tr -d '<' | cut -d ' ' -f 1`"

	echo "${minutes} to go from ${origin} to ${dest}, ${miles} miles in ${minutes} minutes..."
	#echo "\"${origin}\",\"${dest}\",\"${minutes}\",\"${miles}\"" >> ${csv}
	if test x"${origin}" != x; then
	    echo "\"${origin}\",\"${names[$j]}\",\"${minutes}\",\"${miles}\"" >> ${csv}
	fi
	j="`expr $j + 1`"
	if test x"${sources[$j]}" = x""; then
	    break
	fi
    done
#    i="`expr $i + 1`"
    if test x"${senarios[$i]}" = x""; then
	break
    fi
done
