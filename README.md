# osmtools
A handful of bourne shell scripts to produce KML maps from an OSM
database.  I was tasked with producing some offline digital mapping
solutions for my local rural volunteer fire department. Originally I
was limited to downloading maps produced by other people. The problem
with that is I needed to have custom data added. We have a lot of
institutional knowledge of our district, but it's huge. We cover many
hundreds of square miles, most of it national forest or wilderness areas
in this part of the Colorado Rockies.

I eventually decided the way to go was using Open Street Map
data. Initially I was parsing the text files, but that was ay too slow
for most things I wanted to map. I eventually went through the hassle
of downloading and setting up a local copy of the OSM database. Now I
can produce complex maps in a few minutes. The data we're interested
in isn't on any other maps, ie...  unofficial hiking and bike trails,
ski area runs, dispersed camping.

Starting with the existing data has already been useful, but now I'm
uploading updates to Open Street Map. These scripts are pretty crude,
but work for me. :-) Right now two types are supported, 'trails' and
'piste'. I'm working on 'roads' now. Because of the huge amount of data,
I've been using polygons of our local counties to extract subsets of
data. Loading one big file of all the hiking trails in Colorado is too
much for most phones or tablets. County sized files load and display
faster.

As different tyes of ski runs or trails have differing grades, everything
in the KML file is color coded. For Ski runs, they match the acceped
standard colors. For trails, a similar concept is used. Lighter colors
are easy, darker ones are more difficult.

Example:
* read binary OSM data file and load the county data into a new database.
./setupdb.sh mariposa /tmp/california-latest.osm.pbf CA-polyfiles/Mariposa.poly 

* Query the database we've just created for trails or ski runs.
./osm2kml.sh mariposa trails (or piste)

* View the file.
google-earth /tmp/mariposa-trails.kml 

