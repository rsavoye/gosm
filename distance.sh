#!/bin/bash


apikey="AIzaSyCmJWynjNtcpoAY8i_6nsEbmNiox8WlZDg"
url="https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=711 Eureka Street, Black Hawk, CO&destinations=New+York+City,NY&key=AIzaSyCmJWynjNtcpoAY8i_6nsEbmNiox8WlZDg"
otype="xml"			# Can also be json

senarios[0]="711 Eureka Street, Black Hawk, CO"
senarios[1]="1 Dill Pickle Place, Black Hawk, CO"
senarios[2]="286 Norton Drive, Black Hawk, CO"
senarios[3]="30 Trail Dust Road, Black Hawk, CO"
senarios[4]="460 Beethoven Drive, Black Hawk, CO"
senarios[5]="15107 Highway 119, CO"
senarios[6]="19 Old Stagecoach Trail, Rollinville, CO"
senarios[7]="6115 Magnolia Road, CO"
senarios[8]=""			# Terminator


sources[0]="39.80445,-105.52895"		# Hydrant
sources[1]="39.83314,-105.52966"		# Hydrant
sources[2]="39.83970,-105.48030"		# Rec Center
sources[3]="39.86836,-105.46672"		# Ameristar
sources[4]="39.97666,-105.41722"		# Station 1 Cistern
sources[5]="39.83250,-105.43304"		# Eagle Rock
sources[6]=""					# Terminator

names[0]="Hydrant"
names[1]="Hydrant"
names[2]="Gilpin Rec Center"
names[3]="Ameristar Warehouse"
names[4]="Station 1 Cistern"
names[5]="Eagle Rock"

#sources[0]="39.83314999535073,-105.52966998531015" # Rec Center
#sources[1]="39.966359995341257,-105.414719985326144" # TLFPD #1
#sources[2]="39.83249999535078,-105.433049985323592"  # Ameristar

csv="/tmp/distance.csv"
# Create output file
echo "origin,dest,time,miles" > ${csv}

i=0
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
	echo "\"${origin}\",\"${names[$j]}\",\"${minutes}\",\"${miles}\"" >> ${csv}
	j="`expr $j + 1`"
	if test x"${sources[$j]}" = x""; then
	    break
	fi
    done
    i="`expr $i + 1`"
    if test x"${senarios[$i]}" = x""; then
	break
    fi
done
