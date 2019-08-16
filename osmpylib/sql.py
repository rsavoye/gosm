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
from shapely.geometry import GeometryCollection, Point, LineString, Polygon
from shapely import wkt, wkb
from subprocess import PIPE, Popen, STDOUT
import os
import sys
ON_POSIX = 'posix' in sys.builtin_module_names


class Postgis(object):
    """A class to work with a postgresql/postgis database"""

    def __init__(self, dbname=None, dbhost=None):
        #if dbname is not None or dbhost is not None:
        #    self.connect(dbhost, dbname)
        self.database = dbname
        self.dbserver = dbhost

    def connect(self, dbserver='localhost', database='postgres'):
        """Connect to a local or remote postgresql server"""

        self.database = database
        self.dbserver = dbserver
        # Supported parameters for connect are: 
        # *database*: the database name (only as keyword argument)
        # *user*: user name used to authenticate
        # *password*: password used to authenticate
        # *host*: database host address (defaults to UNIX socket if not provided)
        # *port*: connection port number (defaults to 5432 if not provided)
        connect = ""
        if dbserver is not "localhost":
            connect += "host='" + dbserver + "' "
        connect += "dbname='" + database + "'"

        logging.debug("postgresql.connect(%r)" % connect)
        try:
            self.dbshell = psycopg2.connect(connect)
        except psycopg2.OperationalError as e:
            logging.debug("%s doesn't exist! %r" % (database, e.diag.message_primary))

        if self.dbshell.closed == 0:
            self.dbshell.autocommit = True
            logging.info("Opened connection to %r %r" % (database, self.dbshell))

            self.dbcursor = self.dbshell.cursor()
            if self.dbcursor.closed == 0:
                logging.info("Opened cursor in %r %r" % (database, self.dbcursor))
            self.dbcursor = self.dbshell.cursor()
        else:
            logging.warning("DB Shell already open")

    def initDB(self, dbname):
        pg = Postgis()
        pg.connect("localhost", 'postgres')

        pg.query("DROP DATABASE IF EXISTS %s" % dbname)
        pg.query("CREATE DATABASE %s" % dbname)
        # pg.close()

    def query(self, query=""):
        """Query a local or remote postgresql database"""

        # logging.debug("postgresql.query(" + query + ")")
        if self.dbshell.closed != 0:
            logging.error("Database %r is not connected!" % self.options.get('database'))
            return self.result

        self.result = list()
        try:
            self.dbcursor.execute(query)
            # logging.info("Got %r records from query." % self.dbcursor.rowcount)
        except psycopg2.ProgrammingError as e:
            if e.pgcode != None:
                logging.error("Query failed to fetch! %r" % e.pgcode)

        tmp = query.split(' ')
        fields = tmp[1].split(',')
        try:
            line = self.dbcursor.fetchone()
        except:
            return None
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
            self.result.append(data)
            line = self.dbcursor.fetchone()

        return self.result

    def addExtensions(self):
        result = self.query("create extension hstore;")
        result = self.query("create extension postgis;")

    def importOSM(self, filespec="out.osm", dbname=None):
         # ogr2ogr -overwrite -f  "PostgreSQL" PG:"dbname=${dbname}" -nlt GEOMETRYCOLLECTION ${infile}
        if dbname is None:
            dbname = os.path.basename(filespec).replace('.osm', '')
        logging.info("Trying to import %s into database %s" % (filespec, dbname))

        self.initDB(dbname)

        cmd = [ 'ogr2ogr', '-overwrite', '-f', "PostgreSQL", "PG:dbname=" + dbname, "-nlt", "GEOMETRYCOLLECTION", filespec]
        ppp = Popen(cmd, stdout=PIPE, bufsize=0, close_fds=ON_POSIX)
        ppp.wait()

        logging.info("Created database %s with data from %s" % (dbname, filespec))

    def getRoads(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,highway,wkb_geometry FROM lines WHERE highway is not NULL AND (highway!='path' AND highway!='footway' AND highway!='milestone' AND highway!='cycleway' AND highway!='bridleway');")
        return result

    def getAddresses(self, result=list()):
        result = self.query("SELECT osm_id,name,addr_housenumber,addr_street,wkb_geometry FROM points WHERE addr_housenumber is not NULL;")
        return result

    def getTrails(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,highway,wkb_geometry FROM lines WHERE (highway='path' OR highway='footway'  OR highway='cycleway');")
        return result

    def getFireWater(self, result=list()):
        result =  self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM other_relations WHERE other_tags LIKE '%fire_hydrant%' OR other_tags LIKE '%water_tank%' OR other_tags LIKE '%fire_water_pond%';")
        return result

    def getWay(self, geom, result=dict()):
        """Get the data for a fire water source using the GPS location in the relation"""
        result = self.query("SELECT osm_id,emergency,landing_site,name,ref,other_tags FROM points WHERE ST_Equals(ST_CollectionExtract(wkb_geometry, 1), ST_GeomFromText('%s', 4326))" % geom.wkt)
        return result
 
    def getCampGrounds(self, result=list(), campground=None):
        #result = self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM other_relations WHERE other_tags LIKE '%camp_site%' AND name LIKE '%Campground%';")
        result =  self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM other_relations WHERE other_tags LIKE '%camp_site%';")
        return result

    def getCampSites(self, result=list()):
        result = self.query("SELECT osm_id,name,ref,other_tags,wkb_geometry FROM points WHERE tourism='camp_site' OR tourism='camp_pitch';")
        return result

    def getCamp(self, geom, result=list()):
        """Get the data for a campsite using the GPS location in the relation"""
        result = self.query("SELECT osm_id,name,ref,other_tags FROM points WHERE ST_Equals(ST_CollectionExtract(wkb_geometry, 1), ST_GeomFromText('%s', 4326))" % geom.wkt)
        return result
 
    def getPiste(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM lines WHERE other_tags LIKE '%piste%';")
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
        result = self.query("SELECT osm_id,name,description,other_tags FROM points WHERE natural='hot_spring' OR amenity='hot_spring' OR 'bath:type'='hot_spring' OR name LIKE '%Hot Spring%';")
        return result

    def getLandingZones(self, result=list()):
        result = self.query("SELECT osm_id,name,emergency,aeroway,wkb_geometry FROM points WHERE aeroway='helipad' OR aeroway='heliport' OR emergency='landing_site';")
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

