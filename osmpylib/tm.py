#!/usr/bin/python3

# 
#   Copyright (C) 2019   Free Software Foundation, Inc.
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

## \file tiledb.py manage of collection of map tiles.

# ogr2ogr -t_srs EPSG:4326 Roads-new.shp hwy_road_aerial.shp

import os
import sys
import epdb
import logging
import psycopg2
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
from datetime import datetime
from poly import Poly

# {'id': 1, 'project_id': 7, 'x': 420, 'y': 1270, 'zoom': 11, 'extra_properties': None, 'is_square': True, 'ST_GeomFromGeoJSON_1': '{"type": "MultiPolygon", "coordinates": [[[[-106.17187498098184, 39.639537558401855], [-106.17187498098184, 39.77476947931811], [-105.99609373101333, 39.77476947931811], [-105.99609373101333, 39.639537558401855], [-106.17187498098184, 39.639537558401855]]]]}', 'ST_SetSRID_1': 4326, 'task_status': 0, 'locked_by': None, 'mapped_by': None, 'validated_by': None}
class Task(object):
    def __init__(self):
        self.tasks = dict()
        self.tasks['id'] = 0
        self.tasks['project_id'] = 0
        self.tasks['x'] = 0
        self.tasks['y'] = 0
        self.tasks['zoom'] = 0
        self.tasks['extra_properties'] = None
        self.tasks['is_square'] = True
        self.tasks['geometry'] = None
        self.tasks['task_status'] = 0
        self.tasks['locked_by'] = None
        self.tasks['mapped_by'] = None
        self.tasks['validated_by'] = None

    def create(self, id=None, project_id=None, x=0, y=0, zoom=0, geometry=None):
        """Create a Task object with only the values required"""
        if id is None:
            id = self.tasks['id']
        if project_id is None:
            project_id = self.tasks['project_id']
        query="INSERT INTO tasks (id, project_id, x, y, zoom, task_status) VALUES(%d, %d, %d, %d, %d, %d)" % (id, project_id, x, y, zoom, self.tasks['task_status'])

        return query

    def dump(self):
        print("Dumping data from Task class")
        print("\tTask ID:\t%s" % self.tasks['id'])
        print("\tProject ID:\t%s" % self.tasks['project_id'])
        print("\tX:\t\t%s" % self.tasks['x'])
        print("\tY:\t\t%s" % self.tasks['y'])
        print("\tZoom:\t\t%s" % self.tasks['zoom'])
        print("\tIs Square:\t%s" % self.tasks['is_square'])
        print("\tGeometry:\t%s" % self.tasks['geometry'])
        print("\tTask Status:\t%s" % self.tasks['task_status'])
        print("\tLocked By:\t%s" % self.tasks['locked_by'])
        print("\tMapped By:\t%s" % self.tasks['mapped_by'])
        print("\tValidated By:\t%s" % self.tasks['validated_by'])
        print("\tExtra Properties:\t%s" % self.tasks['extra_properties'])


# {'project_id': 7, 'locale': 'en', 'name': 'testsql', 'short_description': None, 'description': None, 'instructions': None, 'project_id_str': None, 'text_searchable': None, 'per_task_instructions': None}
class Info(object):
    def __init__(self):
        self.info = dict()
        self.info['project_id'] = 0
        self.info['locale'] = 'en'
        self.info['name'] = None
        self.info['short_description'] = None
        self.info['description'] = None 
        self.info['instructions'] = None
        self.info['project_id_str'] = None
        self.info['text_searchable'] = None
        self.info['per_task_instructions'] = None

    def create(self, name=None, project_id=0):
        self.info['project_id'] = project_id
        self.info['name'] = name
        if project_id == 0:
            project_id = self.projectid
        query="INSERT INTO project_info (project_id, name, locale) VALUES(%d, '%s', 'en')" % (project_id, name)

        return query

    def dump(self):
        print("Dumping Info class")
        print("\tProject ID:\t%s" % self.info['project_id'])
        print("\tLocale:\t\t%s" % self.info['locale'])
        print("\tName:\t\t%s" % self.info['name'])
        print("\tDescription:\t%s" % self.info['description'])
        print("\tInstructions:\t%s" % self.info['instructions'])
        print("\tProject ID STR:\t%s" % self.info['project_id_str'])
        print("\tText Searchable:\t%s" % self.info['text_searchable'])
        print("\tTask Instructions:\t%s" % self.info['per_task_instructions'])
        print("\tShort Desciption:\t%s" % self.info['short_description'])

# {'status': 2, 'created': datetime.datetime(2019, 6, 6, 15, 32, 47, 680796), 'priority': 2, 'default_locale': 'en', 'author_id': 4606673, 'mapper_level': 1, 'enforce_mapper_level': False, 'enforce_validator_role': False, 'allow_non_beginners': False, 'private': False, 'entities_to_map': None, 'changeset_comment': None, 'osmcha_filter_id': None, 'due_date': None, 'imagery': None, 'josm_preset': None, 'last_updated': datetime.datetime(2019, 6, 6, 15, 32, 47, 634713), 'license_id': None, 'ST_GeomFromGeoJSON_1': '{"type": "MultiPolygon", "coordinates": [[[[-106.0148349220815, 39.88596504944786], [-105.7621493752065, 39.88596504944786], [-105.712710898644, 39.70447940319431], [-106.0473838760935, 39.6482545636245], [-106.0148349220815, 39.88596504944786]]]]}', 'ST_SetSRID_1': 4326, 'task_creation_mode': 0, 'mapping_types': None, 'organisation_tag': None, 'campaign_tag': None, 'mapping_editors': [0, 1, 2, 3], 'validation_editors': [0, 1, 2, 3], 'total_tasks': 6, 'tasks_mapped': 0, 'tasks_validated': 0, 'tasks_bad_imagery': 0}
class Project(object):
    def __init__(self, geometry=None):
        self.project = dict()
        self.project['status'] = 2
        self.project['created'] = datetime.now()
        self.project['priority'] = 2
        self.project['default_locale'] = None
        self.project['author_id'] = uid=4606673
        self.project['mapper_level'] = 1
        self.project['enforce_mapper_level'] = False
        self.project['enforce_validator_role'] = None
        self.project['allow_non_beginners'] = False
        self.project['private'] = False
        self.project['entities_to_map'] = None
        self.project['changeset_comment'] = "#tm-senecass"
        self.project['osmcha_filter_id'] = None
        self.project['due_date'] = None
        self.project['imagery'] = None
        self.project['josm_preset'] = None
        self.project['last_updated'] =  datetime.now()
        self.project['license_id'] = None
        self.project['geometry'] = geometry
        self.project['centroid'] = None
        self.project['task_creation_mode'] = 0
        self.project['mapping_types'] = None
        self.project['organisation_tag'] = "Seneca Software & Solar, Inc."
        self.project['campaign_tag'] = None
        self.project['mapping_editors'] = [0, 1, 2, 3]
        self.project['validation_editors'] = [0, 1, 2, 3]
        self.project['total_tasks'] = 0
        self.project['tasks_mapped'] = 0
        self.project['tasks_validated'] = 0
        self.project['tasks_bad_imagery'] = 0

    def create(self, id, comment=None, polygon=None):
        editors = "{0,1, 2, 3}"
        if comment is None:
            comment = self.project['changeset_comment']
        if polygon is None:
            geometry = self.project['geometry']
        else:
            geometry = polygon.getGeometry()
        self.project['centroid'] = geometry.Centroid().ExportToWkt()
        wkt = polygon.getWkt()
        centroid = geometry.Centroid()
        query="""INSERT INTO projects (id, mapping_editors, validation_editors, total_tasks, tasks_mapped, tasks_validated, tasks_bad_imagery, organisation_tag, changeset_comment, created, status, author_id, mapper_level, task_creation_mode, centroid, geometry) VALUES(%d, %r, %r, %d, %d, %d, %d, '%s', '%s', '%s', %d, %d, %d, %d, ST_Force_2D(ST_GeomFromText('%s', 4326)), ST_Force_2D(ST_GeomFromText('%s', 4326)))""" % (id, editors, editors, 0, 0, 0, 0, self.project['organisation_tag'], comment, self.project['created'], self.project['status'], self.project['author_id'], self.project['mapper_level'], self.project['task_creation_mode'], centroid, geometry)
        return query
        self.dbcursor.execute(query)

    def dump(self):
        print("Dumping data from Project class")

        print("\tOrg Tag:\t%s" % self.project['organisation_tag'])
        print("\tTotal Tasks:\t%s" % self.project['total_tasks'])
        print("\tTasks Mapped:\t%s" % self.project['tasks_mapped'])
        print("\tBad Imagery:\t%s" % self.project['tasks_bad_imagery'])
        print("\tTasks Validated:\t%s" % self.project['tasks_validated'])
        print("\tTask Created:\t%s" % self.project['created'])
        print("\tLast Updated:\t%s" % self.project['last_updated'])

class TM(object):
    def __init__(self):
        self.database = 'tasking-manager'
        # defaults to localhost, current user myst have access permissions
        connect = "dbname='%s'" % self.database
        self.dbshell = psycopg2.connect(connect)
        if self.dbshell.closed == 0:
            self.dbshell.autocommit = True
            logging.info("Opened connection to %r %r" % (self.database, self.dbshell))
            
        self.dbcursor = self.dbshell.cursor()
        if self.dbcursor.closed == 0:
            logging.info("Opened cursor in %r %r" % (self.database, self.dbcursor))
        # Set the next IDs to one past the current max in the database
        query = "SELECT MAX(id) FROM tasks;"
        self.taskid = int(self.query(query)) + 1
        query = "SELECT MAX(id) FROM projects;"
        self.projectid = int(self.query(query)) + 1

    def getNextProjectID(self):
        return self.projectid

    def getNextTaskID(self):
        return self.taskid

    def dump(self):
        print("Dumping data from TM class")
        print("\tTask ID:\t%s" % self.taskid)
        print("\tProject ID:\t%s" % self.projectid)

    def query(self, query):
        if self.dbshell.closed != 0:
            logging.error("Database %s is not connected!" % self.database)
            return self.result

        self.result = list()
        try:
            self.dbcursor.execute(query)
            self.result = self.dbcursor.fetchall()
        except psycopg2.ProgrammingError as e:
            if e.pgcode != None:
                logging.error("Query failed to fetch! %r" % e.pgcode)
        if len(self.result) == 0:
            return ""
        else:
            return self.result[0][0]

