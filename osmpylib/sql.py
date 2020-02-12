#!/usr/bin/python3

#
#  Copyright (C) 2018, 2019, 2020 Free Software Foundation, Inc.
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
import sqlparse
import logging
from shapely.geometry import GeometryCollection, Point, LineString, Polygon
from shapely import wkt, wkb
from subprocess import PIPE, Popen, STDOUT
import os
import sys
ON_POSIX = 'posix' in sys.builtin_module_names
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from poly import Poly


class Postgis(object):
    """A class to work with a postgresql/postgis database"""

    def __init__(self, dbname=None, dbhost=None):
        #if dbname is not None or dbhost is not None:
        #    self.connect(dbhost, dbname)
        self.database = dbname
        self.dbserver = dbhost
        # The geometry is a multipolygon, and limits the query to that area.
        self.boundary = None
        self.dbshell = None
        self.dbcursor = None
        self.fields = list()

    def parse(self, sql):
        for token in sqlparse.parse(sql)[0].tokens:
            if token._get_repr_name() == "IdentifierList":
                for ident in token.get_identifiers():
                    logging.debug("IDENT: %r" % ident.get_name())
                    self.fields.append(ident.get_name())
                    # logging.info("TOKEN: %r %s" % (token, type(token)))
        return self.fields

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
        if dbserver != "localhost":
            connect += "host='" + dbserver + "' "
        connect += "dbname='" + database + "'"

        logging.debug("postgresql.connect(%r)" % connect)
        try:
            self.dbshell = psycopg2.connect(connect)
        except psycopg2.OperationalError as e:
            logging.debug("%s doesn't exist! %r" % (database, e.diag.message_primary))

        if self.dbshell is None:
            logging.error("There is no database %s" % database)
            quit()

        if self.dbshell.closed == 0:
            self.dbshell.autocommit = True
            logging.info("Opened connection to %r %r" % (database, self.dbshell))

            self.dbcursor = self.dbshell.cursor()
            if self.dbcursor.closed == 0:
                logging.info("Opened cursor in %r %r" % (database, self.dbcursor))
            self.dbcursor = self.dbshell.cursor()
        else:
            logging.warning("DB Shell already open")
        # self.addExtensions()

    def addPolygon(self, poly):
        wkt = poly.getGeometry().getWkt()
        self.boundpoints = "AND ST_Contains(ST_GeomFromText(%s, 4326), ST_CollectionExtract(wkb_geometry, 1))" % wkt
        self.boundlines = "AND ST_Contains(ST_GeomFromText(%s, 4326), ST_CollectionExtract(wkb_geometry, 2))" % wkt

    def close(self):
        self.dbshell.close()

    def initDB(self, dbname):
        """Remove and recreate the database to avoid problems"""
        pg = Postgis()
        pg.connect("localhost", 'postgres')

        logging.debug("Adding default extensions to %s" % dbname)
        pg.query("DROP DATABASE IF EXISTS %s" % dbname)
        pg.query("CREATE DATABASE %s" % dbname)
        pg.close()

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
                logging.error("Query failed to fetch! %r" % e.pgerror)

        tmp = query.split(' ')
        logging.debug("FIXME fields(%d): %r" % (self.dbcursor.rowcount, tmp))
        fields = self.parse(query)
        
        # fields = tmp[1].split(',')
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
                    try:
                        data['wkb_geometry'] = wkb.loads(item,hex=True)
                    except:
                        logging.warning("Couldn't parse %r" % data['name'])
                        i += 1
                        continue
                    #data['wkb_geometry'] = wkb.loads(item.tobytes())
                else:
                    data[fields[i]] = item
                i += 1
            self.result.append(data)
            line = self.dbcursor.fetchone()

        return self.result

    # Edit /usr/share/gdal/osmconf.ini and add boundary as a polygon
    def getBoundaries(self, poly, result=list()):
        result = self.query("")
        self.addPolygon(poly)
#        result =  self.query("SELECT osm_id,name,boundary,wkb_geometry FROM multipolygons WHERE boundary is not NULL';")
        return self.result

        return result

    def addExtensions(self):
        result = self.query("create extension hstore")
        result = self.query("create extension postgis")

    def importOSM(self, filespec="out.osm", dbname=None):
        # FIXME: there has got to be a somple way of doing this purely
        # in python using ogr, and not using a subprocess.
         # ogr2ogr -overwrite -f  "PostgreSQL" PG:"dbname=${dbname}" -nlt GEOMETRYCOLLECTION ${infile}
        if dbname is None:
            dbname = os.path.basename(filespec).replace('.osm', '')
        logging.info("Trying to import %s into database %s" % (filespec, dbname))

        # self.initDB(dbname)

        cmd = [ 'ogr2ogr', '-overwrite', '-f', "PostgreSQL", "PG:dbname=" + dbname, "-nlt", "GEOMETRYCOLLECTION", filespec]
        ppp = Popen(cmd, stdout=PIPE, bufsize=0, close_fds=ON_POSIX)
        ppp.wait()

        logging.info("Created database %s with data from %s" % (dbname, filespec))

    def getRoads(self, result=list()):
        result = self.query("SELECT osm_id,name,other_tags,highway,wkb_geometry FROM lines WHERE highway is not NULL AND (highway!='path' AND highway!='footway' AND highway!='milestone' AND highway!='cycleway' AND highway!='bridleway');")
        return result

    def getAddresses(self, geom, result=list()):
        """Get all the addresses in a defined area"""
        result = self.query("SELECT osm_id,name,addr_housenumber,addr_street,wkb_geometry FROM points WHERE ST_Contains(ST_GeomFromText('%s', 4326), ST_CollectionExtract(wkb_geometry, 1)) AND addr_housenumber is not NULL;" % geom.wkt)
        return result

    def getWay(self, geom, result=dict()):
        """Get the data for a fire water source using the GPS location in the relation"""
        result = self.query("SELECT osm_id,emergency,landing_site,name,ref,other_tags FROM points WHERE ST_Equals(ST_CollectionExtract(wkb_geometry, 1), ST_GeomFromText('%s', 4326))" % geom.wkt)
        return result
 
    def getCampGrounds(self, result=list(), campground=None):
        """Get all the camping areas in the database, which is used to organize them
        the camp sites into each campground"""
        #result = self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM other_relations WHERE other_tags LIKE '%camp_site%' AND (name LIKE '%Campground%' OR name LIKE '%Camping Area%' );")
        result =  self.query("SELECT osm_id,name,other_tags,wkb_geometry FROM multipolygons WHERE tourism='camp_site' AND boundary is not NULL;")
        return result

    def getCampSites(self, geom, result=list()):
        """Get all the camp sites in a camping area"""
        result = self.query("SELECT osm_id,ref,name,other_tags,wkb_geometry FROM points WHERE ST_Contains(ST_GeomFromText('%s', 4326), ST_CollectionExtract(wkb_geometry, 1)) AND (tourism='camp_pitch' OR tourism='camp_site');" % geom.wkt)
        return result

    def getPlaces(self, level, result=list()):
        """Get all the cities and town in the database, which is used to organize
        various data into smaller, more navigatable subsets."""
        result =  self.query("SELECT osm_id,osm_way_id,name,admin_level,place,wkb_geometry FROM multipolygons WHERE boundary is not NULL AND admin_level='%d' AND name is not NULL;" % level)
        return result

    def getProtected(self, result=list()):
        """Get all the wilderness areas and park in database, which is used to organize
        various data into smaller, more navigatable subsets."""
        result =  self.query("SELECT osm_id,osm_way_id,name,admin_level,place,wkb_geometry FROM multipolygons WHERE boundary='protected_area' OR boundary='national_park' AND name is not NULL;")
        return result

    def getTrails(self, geom, result=list()):
        """Get all the Trails in a defined area"""
        result = self.query("SELECT osm_id,name,highway,other_tags,wkb_geometry FROM lines WHERE ST_Contains(ST_GeomFromText('%s', 4326), ST_CollectionExtract(wkb_geometry, 2)) AND highway='path';" % geom.wkt)
        return result

    def getFireWater(self, geom, result=list()):
        """Get all the fire hydrants, cisterns, or open water sources in a polygon."""
        query = "SELECT osm_id,ref,name,emergency,wkb_geometry FROM points WHERE ST_Contains(ST_GeomFromText('%s', 4326), ST_CollectionExtract(wkb_geometry, 1)) AND (emergency='fire_hydrant' OR emergency='water_tank' OR emergency='fire_water_pond');" % geom[0].wkt
        result = self.query(query)
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

