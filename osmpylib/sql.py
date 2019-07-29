#!/usr/bin/python3

#
#   Copyright (C) 2018,2019 Free Software Foundation, Inc.
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

## \copyright GNU Public License.
## \file sql.py Wrapper for the psycopg2 module

import epdb
import psycopg2
import logging
from maptypes import MapType


class Postgis(object):
    """A class to work with a postgresql/postgis database"""

    def __init__(self):
        self.database = None
        self.dbserver = None

    def connect(self, dbserver, database):
        """Connect to a local or remote postgresql server"""

        # Supported parameters for connect are: 
        # *database*: the database name (only as keyword argument)
        # *user*: user name used to authenticate
        # *password*: password used to authenticate
        # *host*: database host address (defaults to UNIX socket if not provided)
        # *port*: connection port number (defaults to 5432 if not provided)
        connect = ""
        if dbserver is not "localhost":
            connect += "host='" + dbserver + "'"
        connect += " dbname='" + database + "'"

        logging.debug("postgresql.connect(%r)" % connect)
        self.dbshell = psycopg2.connect(connect)
        if self.dbshell.closed == 0:
            self.dbshell.autocommit = True
            logging.info("Opened connection to %r %r" % (database, self.dbshell))

            self.dbcursor = self.dbshell.cursor()
            if self.dbcursor.closed == 0:
                logging.info("Opened cursor in %r %r" % (database, self.dbcursor))

    def query(self, query=""):
        """Query a local or remote postgresql database"""

        logging.debug("postgresql.query(" + query + ")")
        if self.dbshell.closed != 0:
            logging.error("Database %r is not connected!" % self.options.get('database'))
            return self.result

        self.result = list()
        try:
            self.dbcursor.execute(query)
        except psycopg2.ProgrammingError as e:
            if e.pgcode != None:
                logging.error("Query failed to fetch! %r" % e.pgcode)

    def count(self, type):
        if type is "roads":
            sql = "COUNT(*) FROM planet_osm_line WHERE highway is not NULL AND highway!='path' OR highway!='footway' OR highway!='cycleway"
        elif type is "trails":
            sql = "COUNT(*) FROM planet_osm_line WHERE highway='path' OR highway='footway' OR highway='cycleway"
        elif type is "huts":
            sql = "osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber' from planet_osm_point WHERE tourism='wilderness_hut' OR tourism='alpine_hut"

# --command="SELECT count(*) FROM planet_osm_point WHERE tourism='hotel' OR tourism='hostel' OR tourism='guest_house'" | tr -d ' '`"
# --command="SELECT count(*) FROM planet_osm_point WHERE natural='peak'" | tr -d ' '`"
# --command="SELECT count(*) FROM planet_osm_point WHERE place='hamlet' OR place='village' OR place='town' OR place='isolated_dwelling' OR place='locality'" | tr -d ' '`"
# --command="SELECT count(*) FROM planet_osm_point WHERE tags->'sport'='swimming' AND tags->'amenity'!='swimming_pool'" | tr -d ' '`"#
# --command="SELECT count(*) FROM planet_osm_point WHERE historic is not NULL" | tr -d ' '`"
# --command="SELECT count(*) FROM planet_osm_point WHERE tourism='camp_site' OR  amenity='campground'"  | tr -d ' '`"
#--command="SELECT COUNT(*) FROM planet_osm_point WHERE tags->'emergency'='fire_hydrant' OR tags->'emergency'='water_tank'" | tr -d ' '`"
# --command="SELECT COUNT(*) FROM planet_osm_point WHERE tags->'aeroway'='helipad' OR tags->'emergency'='landing_site'" | tr -d ' '`"
# --command="SELECT COUNT(*) FROM planet_osm_point WHERE tags->'emergency'='fire_station'" | tr -d ' '`"
# --command="SELECT count(*) FROM planet_osm_line WHERE tags->'piste:type' is not NULL" | tr -d ' '`"
# --command="SELECT count(*) FROM planet_osm_point WHERE 'addr:housenumber' is not NULL" | tr -d ' '`"
# --command="SELECT count(*) FROM planet_osm_point WHERE milestone is not NULL" | tr -d ' '`" -f /tmp/foo-$$.sql`"
# --command="SELECT count(*) FROM planet_osm_point WHERE amenity='parking' AND name LIKE '%Trailhead'" | tr -d ' '`"


    def getRoads(self, result=list()):
#        self.query("osm_id,name,wkb_gemetry,highway,other_tags from lines WHERE (highway IS NOT NULL) AND (highway!='path' AND ighway!='footway' AND highway!='cycleway' AND highway!='driveway'")
        self.query("SELECT osm_id,name,wkb_geometry,highway,other_tags from lines WHERE (highway!='path' AND highway!='footway');")
        line = self.dbcursor.fetchone()
        while line is not None:
            road = dict()
            road['osm_id'] = line[0]
            road['name'] = line[1] 
            road['way'] = line[2]
            road['highway'] = line[3]
            if line[4] is not None:
                tags = line[4].split(',')
                for item in tags:
                    print(item)
                    tmp = item.split('=>')
                    print(len(tmp))
                    if len(tmp) == 2:
                        print(tmp[1])
                        road[tmp[0]] = tmp[1]
            line = self.dbcursor.fetchone()
            result.append(road)
        print(self.dbcursor.rowcount)
#line.osm_id,line.name,ST_AsKML(line.way),line.tags->'addr:full',tags->'adrr:street',tags->'addr:housenumber',tags->'alt_name',tags->'addr:full' from planet_osm_line AS line;
#line.osm_id,line.name,ST_AsKML(line.way) from planet_osm_line AS line;
#line.osm_id,line.name,line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access,ST_AsKML(line.way) FROM planet_osm_line AS line, dblink('dbname=polygons', 'select name,geom FROM boundary') AS poly(name name,geom geometry) WHERE poly.name='${polygon}' AND (ST_Crosses(line.way,poly.geom) OR ST_Contains(poly.geom,line.way)) AND (line.highway='footway' OR line.highway = 'path');
#line.osm_id,line.name,ST_AsKML(line.way),line.tags->'sac_scale',line.tags->'bicycle',line.tags->'mtb:scale:imba',line.access FROM planet_osm_line AS line WHERE line.highway='footway' OR line.highway = 'path' OR line.highway = 'cycleway';
#line.osm_id,line.name,ST_AsKML(line.way),line.tags->'piste:type',line.tags->'piste:difficulty',line.tags->'piste:grooming',line.aerialway,line.access FROM planet_osm_line AS line WHERE line.tags->'piste:type' is not NULL
#osm_id,name,ST_AsKML(way) from planet_osm_point WHERE (highway='trailhead' OR leisure='trailhead' OR amenity='trailhead') AND name LIKE '%Trailhead';
#osm_id,name,ST_AsKML(way) from planet_osm_polygon WHERE amenity='parking' AND name LIKE '%Trailhead';
#SELECT name FROM planet_osm_polygon WHERE tags->'is_in'!='' AND tourism='camp_site';
# osm_id,name,ST_AsKML(way),tags->'fee',tags->'toilets',tags->'website',tags->'operator',tags->'sites',amenity,leisure,tourism,tags->'is_in' from planet_osm_point WHERE tourism='camp_site' OR amenity='campground' ORDER BY tags->'is_in';
# osm_id,name,ST_AsKML(way),tags->'alt_name' from planet_osm_point WHERE highway='milestone';
# osm_id,name,ST_AsKML(way),historic from planet_osm_point WHERE historic is not NULL;
# osm_id,name,ST_AsKML(way),ele FROM planet_osm_point WHERE natural='peak';
# osm_id,ST_AsKML(way),"addr:housenumber",tags->'addr:street',tags->'addr:full' FROM planet_osm_point WHERE tags->'addr:street'!='' AND 'addr:housenumber' is not NULL;
# osm_id,ST_AsKML(ST_Centroid(way)),'addr:housenumber',tags->'addr:street',tags->'addr:full' FROM planet_osm_polygon WHERE tags->'addr:street'!='' AND 'addr:housenumber' is not NULL AND building='yes';
# osm_id,name,ST_AsKML(way),tags->'description' FROM planet_osm_point WHERE "natural"='hot_spring' OR "leisure"='hot_spring' OR "amenity"='hot_spring' OR 'bath:type'='hot_spring' OR name LIKE '%Hot%' ;
# osm_id,name,ST_AsKML(way),tags->'emergency',tags->'aeroway' from planet_osm_point WHERE aeroway='helipad' OR aeroway='heliport' OR tags->'emergency'='landing_site' ${polysql};
# osm_id,name,ST_AsKML(way),tags->'emergency',tags->'fire_hydrant:type',tags->'fire_hydrant:diameter',water,tags->'water_tank:volume',tags->'note',disused,tags->'is_in' from planet_osm_point WHERE tags->'emergency'='fire_hydrant' OR tags->'emergency'='water_tank' ORDER BY tags->'is_in';
# osm_id,name,ST_AsKML(way),amenity,tags->'emergency' from planet_osm_point WHERE tags->'emergency'!='';
# sql.sh 323:SELECT osm_id,name,ST_AsKML(way) from planet_osm_point WHERE tags->'internet_access'='wlan';
# osm_id,name,ST_AsKML(way),tags->'name.en',tags->'description' from planet_osm_point WHERE waterway='waterfall';
# osm_id,name,ST_AsKML(way),name.en,description from planet_osm_point WHERE tags->'sport'='swimming' AND tags->'amenity'!='swimming_pool' ${polysql};
# sql.sh 338:SELECT osm_id,name,ST_AsKML(way),name.en,description from planet_osm_point WHERE tags->'sport'='climbing'' ${polysql};
# osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber' from planet_osm_point WHERE tourism='wilderness_hut' OR tourism='alpine_hut' ${polysql};
# osm_id,name,ST_AsKML(way),place from planet_osm_point WHERE place='hamlet' OR place='village' OR place='town' OR place='isolated_dwelling' OR place='locality';
# osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber',tags->'name:en' from planet_osm_point WHERE tourism='hotel' OR tourism='hostel' OR tourism='guest_house' ${polysql};
# #osm_id,name,tags->'alt_name',tags->'addr:state',ST_AsKML(way) FROM planet_osm_line SORT WHERE boundary='administrative' AND name!='';
 
post = Postgis()
post.connect('localhost', 'TimberlineFireProtectionDistrict')
post.getRoads()
