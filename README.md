# gosm

This started as a handful of bourne shell scripts to produce KML maps
from an OSM  database. I was tasked with producing some offline
digital mapping solutions for my local rural volunteer fire
department. Originally I was limited to downloading maps produced by
other people. The problem with that is we needed to have our custom
data added. We have a lot of institutional knowledge of our district,
but it's huge. We cover many hundreds of square miles, most of it
national forest or wilderness areas in this part of the Colorado
Rockies. The data we're interested in isn't on any other maps, ie...
unofficial hiking and bike trails, ski area runs, dispersed camping.

I eventually decided the way to go was using Open Street Map
data. Initially I was parsing the text files, but that was way too slow
for most things I wanted to map. I eventually went through the hassle
of downloading and setting up a local copy of the OSM database. Now I
can produce complex maps in a few minutes.

Starting with the existing data has already been useful, but now I'm
uploading updates to Open Street Map. These scripts are pretty crude,
but work for me, and should be easily hackable. :-) Because of the
huge amount of data, I've been using polygons of 
our local counties to extract subsets of data. Loading one big file of
all the hiking trails in Colorado is too much for most phones or
tablets. County sized files load and display faster.

As different tyes of ski runs, hiking trails, and bike trails have
differing grades, everything in the KML file is color coded. For Ski
runs, they match the acceped standard colors. For trails, a similar
concept is used based on interntional "standards". Unfortunately the
scales for hiking and mountain biking for most trails aren't in the
database. I've been adding the proper scales for my fire department's
response areas, since it's useful for backcountry rescues. The two
tags are only recently approved, 'sac_scale' and 'mtn:scale:imba', so
hopefully over time this data will get filled in. The ratings usually
have to come from another source, like park maps, hiking or biking
organizations, or local knowledge.

Example:
* read binary OSM data file and load the county data into a new database.
./setupdb.sh --infile mariposa /tmp/california-latest.osm.pbf --polyfile CA-polyfiles/Mariposa.poly 

* Query the database we've just created for trails,ski runs, and
landing ones.
./osm2kml.sh --database Mariposa --subset trails,piste,helicopter --output Mariposa.kml

* View the file.
google-earth /tmp/Mariposa.kml

* Extract specific Placemarks based on a regular expression.
./kmltool.py -v -i firestuff.kml -e "name.*Eagle Rock","name.*Center"

* Split a KML file into seperate files based on each KML Folder.
./kmltool.py -v -i firestuff.kml -s

* Join multiple KML files into a single file
./kmltool.py -v -i firestuff.kml,hiking.kml,roads,kml -o bigmap.kml

* Convert a KML file containing a polygon to an OSM .poly file.
./kml2poly.sh infile.kml

* Read a .polyfile into an postgresql database
./polyin,sh --database Utah --operation trail

* Convert a Shapefile into an OSM file.
./shp2map.py --infile foo.shp --convfile utahgis.conv --outfile utah.osm

*  Often a shapefile is in a different coordinate system, so it it
   looks weird, convert it to 4326, which is standard.
ogr2ogr -t_srs EPSG:4326 fixed.shp orig.shp
