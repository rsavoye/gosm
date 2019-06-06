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

import operator
import os
import sys
import logging
import epdb
import psycopg2
from urllib.parse import urlparse
from sys import argv
sys.path.append(os.path.dirname(argv[0]) + '/osmpylib')
import filetype


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

    def create(self):
        self.tasks['id'] = 0
        self.tasks['project_id'] = 0
        self.tasks['x'] = 0
        self.tasks['y'] = 0
        self.tasks['zoom'] = 0
        self.tasks['geometry'] = None


# {'project_id': 7, 'locale': 'en', 'name': 'testsql', 'short_description': None, 'description': None, 'instructions': None, 'project_id_str': None, 'text_searchable': None, 'per_task_instructions': None}
class Info(object):
    def __init__(self):
        self.info = dict()
        self.info['project_id'] = 0
        self.info['locale'] = None
        self.info['name'] = None
        self.info['short_description'] = None
        self.info['description'] = None 
        self.info['instructions'] = None
        self.info['project_id_str'] = None
        self.info['text_searchable'] = None
        self.info['per_task_instructions'] = None

    def create(self, name):
        self.info['project_id'] = 0
        self.info['locale'] = "en"
        self.info['name'] = name


# {'status': 2, 'created': datetime.datetime(2019, 6, 6, 15, 32, 47, 680796), 'priority': 2, 'default_locale': 'en', 'author_id': 4606673, 'mapper_level': 1, 'enforce_mapper_level': False, 'enforce_validator_role': False, 'allow_non_beginners': False, 'private': False, 'entities_to_map': None, 'changeset_comment': None, 'osmcha_filter_id': None, 'due_date': None, 'imagery': None, 'josm_preset': None, 'last_updated': datetime.datetime(2019, 6, 6, 15, 32, 47, 634713), 'license_id': None, 'ST_GeomFromGeoJSON_1': '{"type": "MultiPolygon", "coordinates": [[[[-106.0148349220815, 39.88596504944786], [-105.7621493752065, 39.88596504944786], [-105.712710898644, 39.70447940319431], [-106.0473838760935, 39.6482545636245], [-106.0148349220815, 39.88596504944786]]]]}', 'ST_SetSRID_1': 4326, 'task_creation_mode': 0, 'mapping_types': None, 'organisation_tag': None, 'campaign_tag': None, 'mapping_editors': [0, 1, 2, 3], 'validation_editors': [0, 1, 2, 3], 'total_tasks': 6, 'tasks_mapped': 0, 'tasks_validated': 0, 'tasks_bad_imagery': 0}
class Project(object):
    def __init__(self):
        self.project = dict()
        self.project['status'] = None
        self.project['created'] = None
        self.project['priority'] = None
        self.project['default_locale'] = None
        self.project['author_id'] = None
        self.project['mapper_level'] = None
        self.project['enforce_mapper_level'] = None
        self.project['enforce_validator_role'] = None
        self.project['allow_non_beginners'] = None
        self.project['private'] = None
        self.project['entities_to_map'] = None
        self.project['changeset_comment'] = None
        self.project['osmcha_filter_id'] = None
        self.project['due_date'] = None
        self.project['imagery'] = None
        self.project['josm_preset'] = None
        self.project['last_updated'] = None
        self.project['license_id'] = None
        self.project['geometry'] = None
        self.project['centroid'] = None
        self.project['task_creation_mode'] = None
        self.project['mapping_types'] = None
        self.project['organisation_tag'] = None
        self.project['campaign_tag'] = None
        self.project['mapping_editors'] = None
        self.project['validation_editors'] = None
        self.project['total_tasks'] = None
        self.project['tasks_mapped'] = None
        self.project['tasks_validated'] = None
        self.project['tasks_bad_imagery'] = None

class TM(object):
    def __init__(self):
        database = 'tasking-manager'
        # defaults to localhost, current user myst have access permissions
        connect = "dbname='%s'" % database
        self.dbshell = psycopg2.connect(connect)
        if self.dbshell.closed == 0:
            self.dbshell.autocommit = True
            logging.info("Opened connection to %r %r" % (database, self.dbshell))
            
        self.dbcursor = self.dbshell.cursor()
        if self.dbcursor.closed == 0:
            logging.info("Opened cursor in %r %r" % (database, self.dbcursor))
        query = "SELECT MAX(id) FROM tasks;"
        self.taskid = int(self.query(query)) + 1
        query = "SELECT MAX(id) FROM projects;"
        self.projectid = int(self.query(query)) + 1

    def dump(self):
        print(self.taskid)
        print(self.projectid)

    def query(self, query):
        if self.dbshell.closed != 0:
            logging.error("Database %s is not connected!" % database)
            return self.result

        self.result = list()
        try:
            self.dbcursor.execute(query)
            self.result = self.dbcursor.fetchall()
        except psycopg2.ProgrammingError as e:
            if e.pgcode != None:
                logging.error("Query failed to fetch! %r" % e.pgcode)
        return self.result[0][0]

    def insert_task(self, task):
        sql="INSERT INTO tasks (id, project_id, x, y, zoom, extra_properties, is_square, geometry, task_status, locked_by, mapped_by, validated_by) VALUES (%(id)s, %(project_id)s, %(x)s, %(y)s, %(zoom)s, %(extra_properties)s, %(is_square)s, ST_SetSRID(ST_GeomFromGeoJSON(%(ST_GeomFromGeoJSON_1)s), %(ST_SetSRID_1)s), %(task_status)s, %(locked_by)s, %(mapped_by)s, %(validated_by)s)"

    def insert_project(self, project):
        sql="INSERT INTO projects (status, created, priority, default_locale, author_id, mapper_level, enforce_mapper_level, enforce_validator_role, allow_non_beginners, private, entities_to_map, changeset_comment, osmcha_filter_id, due_date, imagery, josm_preset, last_updated, license_id, geometry, centroid, task_creation_mode, mapping_types, organisation_tag, campaign_tag, mapping_editors, validation_editors, total_tasks, tasks_mapped, tasks_validated, tasks_bad_imagery) VALUES (%(status)s, %(created)s, %(priority)s, %(default_locale)s, %(author_id)s, %(mapper_level)s, %(enforce_mapper_level)s, %(enforce_validator_role)s, %(allow_non_beginners)s, %(private)s, %(entities_to_map)s, %(changeset_comment)s, %(osmcha_filter_id)s, %(due_date)s, %(imagery)s, %(josm_preset)s, %(last_updated)s, %(license_id)s, ST_SetSRID(ST_GeomFromGeoJSON(%(ST_GeomFromGeoJSON_1)s), %(ST_SetSRID_1)s), ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(%(ST_GeomFromGeoJSON_1)s), %(ST_SetSRID_1)s)), %(task_creation_mode)s, %(mapping_types)s, %(organisation_tag)s, %(campaign_tag)s, %(mapping_editors)s, %(validation_editors)s, %(total_tasks)s, %(tasks_mapped)s, %(tasks_validated)s, %(tasks_bad_imagery)s) RETURNING projects.id"

    def insert_info(self, info):
        sql="""INSERT INTO project_info (project_id, locale, name, short_description, d
escription, instructions, project_id_str, text_searchable, per_task_instructions)
	    VALUES (%(project_id)s, %(locale)s, %(name)s, %(short_description)s, %(description)s, %(instructions)s, %(project_id_str)s, %(text_searchable)s, %(per_task_instructions)s)"""

if __name__ == '__main__':
    tm = TM()
    tm.dump()
    task = Task()
    info = Info()
    project = Project()
