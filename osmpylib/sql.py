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
from io import BytesIO
from shapely.geometry import GeometryCollection, Point, LineString, Polygon
from shapely import wkt, wkb
import ppygis3


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
            logging.info("Got %r records from query." % self.dbcursor.rowcount)
        except psycopg2.ProgrammingError as e:
            if e.pgcode != None:
                logging.error("Query failed to fetch! %r" % e.pgcode)

#        for row in self.dbcursor:
#            i = 0
#            for item in row:
#                print(row[i])
#                i += 1

#        buffer = BytesIO()
#        self.dbcursor.copy_to(buffer, '')
#        buffer.seek(0)
#        for line in buffer:
#            print(Geometry.read_ewkb(line.strip()))

        tmp = query.split(' ')
        fields = tmp[1].split(',')
        line = self.dbcursor.fetchone()
        while line is not None:
            i = 0
            data = dict()
            for item in line:
                if fields[i] == "other_tags":
                    if item is not None:
                        tags = item.split(',')
                        for value in tags:
                            # print(value)
                            tmp = value.split('=>')
                            # print(len(tmp))
                            if len(tmp) == 2:
                                # print(tmp[1])
                                data[tmp[0].replace('"', '')] = tmp[1].replace('"', '')
                elif fields[i] == "wkb_geometry":
                    data['wkb_geometry'] = wkb.loads(item,hex=True)
                else:
                    data[fields[i]] = item
                i += 1
            # FIXME: convert Collection to points
            #print(data)
            self.result.append(data)
            line = self.dbcursor.fetchone()

        return self.result

    def count(self, type):
        if type is "roads":
            sql = "COUNT(*) FROM planet_osm_line WHERE highway is not NULL AND highway!='path' OR highway!='footway' OR highway!='cycleway"
        elif type is "trails":
            sql = "COUNT(*) FROM planet_osm_line WHERE highway='path' OR highway='footway' OR highway='cycleway"
        elif type is "huts":
            sql = "osm_id,name,ST_AsKML(way),tourism,tags->'phone',tags->'email',tags->'website',tags->'addr:street',tags->'addr:housenumber' from planet_osm_point WHERE tourism='wilderness_hut' OR tourism='alpine_hut"

    def getRoads(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,highway,wkb_geometry FROM lines WHERE highway is not NULL AND (highway!='path' AND highway!='footway' AND highway!='milestone' AND highway!='cycleway' AND highway!='bridleway');")
        return result

    def getAddresses(self, result=list()):
        result = self.query("SELECT osm_id,name,addr_housenumber,addr_street,wkb_geometry FROM points WHERE addr_housenumber is not NULL;")
        return result

    def getTrails(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,highway,wkb_geometry FROM lines WHERE (highway='path' OR highway='footway'  OR highway='cycleway');")
        return result

    def getCampGrounds(self, result=list(), campground=None):
        #result = self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM other_relations WHERE other_tags LIKE '%camp_site%' AND name LIKE '%Campground%';")
        result =  self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM other_relations WHERE other_tags LIKE '%camp_site%';")
        return result

    def getCampSites(self, result=list()):
        result = self.query("SELECT osm_id,name,ref,other_tags,wkb_geometry FROM points WHERE tourism='camp_site' OR tourism='camp_pitch';")
        return result

    def getCamp(self, geom, result=list()):
        result = self.query("SELECT osm_id,name,ref,other_tags FROM points WHERE ST_Equals(ST_CollectionExtract(wkb_geometry, 1), ST_GeomFromText('%s', 4326))" % geom.wkt)
        return result
 
    def getPiste(self, result=list()):
        result = self.query("")
        return result
    
    def getHistoric(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,historic,wkb_geometry FROM points WHERE historic is not NULL;")
        return result

    def getMilestones(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM points WHERE highway='milestone';")
        return result

    def getTrailhead(self, result=list()):
        result = self.query("")
        return result

    def getHotSprings(self, result=list()):
        # result = self.query("SELECT osm_id,name,description,wkb_geometry FROM points WHERE "natural"='hot_spring' OR "leisure"='hot_spring' OR "amenity"='hot_spring' OR 'bath:type'='hot_spring' OR name LIKE '%Hot%' ;")
        return result

    def getLandingZones(self, result=list()):
        result = self.query("SELECT osm_id,name,emergency,aeroway,wkb_geometry FROM points WHERE aeroway='helipad' OR aeroway='heliport' OR emergency='landing_site';")
        return result

    def getFireWater(self, result=list()):
        result = self.query("SELECT osm_id,name,emergency,water_tank,is_in,wkb_geometry from points WHERE emergency='fire_hydrant' OR emergency='water_tank' OR water_tank IS NOT NULL  AND disused!='yes' ORDER BY is_in;")
        return result

    def getPlace(self, result=list()):
        result = self.query("osm_id,name,place,wkb_geometry FROM points WHERE place='hamlet' OR place='village' OR place='town' OR place='isolated_dwelling' OR place='locality';")
        return result

    def getWaterfalls(self, result=list()):
        result = self.query("")
        return result

    def getLodging(self, result=list()):
        result = self.query("")
        return result

