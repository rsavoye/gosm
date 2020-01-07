#!/usr/bin/python3

# 
# Copyright (C) 2017, 2018, 2019, 2020   Free Software Foundation, Inc.
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

import pdb
import glob
import psycopg2
import subprocess
import config
import logging
from shapely.geometry import MultiPolygon


class pgdb(object):
    """PostgreSQL database class."""
    def __init__(self, config):
        self.config = config
        self.dbname = ""
        self.result = ""
        # self.config.dump()
# Load the SQL functions from osmsqllib
        self.load_functions()
        self.geometry = None
        #self.geometry =  MultiPolygon()

    def connect(self, dbname):
        logging.debug("plotcalls.connect(" + dbname + ")")
        self.config.set('dbname', dbname)
        #connect =  " host=" + self.config.get('dbhost')
        #connect += " user=" + self.config.get('dbuser')
        #connect += " password=" + self.config.get('dbpass')
        connect = " dbname=" + dbname
        
        try:
            self.dbshell = psycopg2.connect(connect)
            if self.dbshell.closed == 0:
                self.dbshell.autocommit = True
                logging.info("Opened connection to %r %r" % (dbname, self.dbshell))
                
                self.dbcursor = self.dbshell.cursor()
                if self.dbcursor.closed == 0:
                    logging.info("Opened cursor in %r %r" % (dbname, self.dbcursor))

        except Exception as e:
            print("Couldn't connect to database: %r" % e)
        
    # List the SQL functions in a database
    # func = optional function name to limit the results
    def list_functions(self, func=''):
        cmdline = list()
        cmdline.append("psql")
        cmdline.append("--dbname=" + self.dbname)
        cmdline.append("--command=\df " + func)
        try:
            subprocess.call(cmdline, stdout=subprocess.DEVNULL)
        except:
            self.verbose.warning("Couldn't list function: %r" % func)
            out = False
            
        return True

    # Load all the SQL files that define our functions
    def load_functions(self):
        top = self.config.get('toplevel')
        files = list()
        try:
            files = glob.glob(top + "/*.sql")
        except Exception as inst:
            logging.error(inst)
            return
            
        for file in files:
            cmdline = list()
            cmdline.append("psql")
            cmdline.append("--dbname=" + self.dbname)
            cmdline.append("--file=" + file)
            self.verbose.log("Loading SQL functions from file: %r" % file)
            try:
                subprocess.call(cmdline, stdout=subprocess.DEVNULL)
            except:
                logging.warning("Couldn't load: %r" + file)
                return False

        return True

    # Get a list of all the SQL functions in a sub directory. This assumes
    # one function per file.
    def get_functions(self):
        top = self.config.get('toplevel')
        files = list()
        functions = list()
        files = glob.glob(top + "/*.sql")
        for sqlfile in files:
            file = open(sqlfile, "r")
            line = file.readline().split(' ')
            last = len(line) - 1
            functions.append(line[last].replace('()\n', ''))
            file.close()

        return functions

    def query(self, query, nores=""):
        logging.debug("plotcalls.query(" + query + ")")
        try:
            self.dbcursor.execute(query)
            self.result = self.dbcursor.fetchall()
        except:
            self.result = list()
        #logging.debug("FIXME: query(%r)" % len(self.result))
        nores = self.result
        return self.result

    def shell(self, cmd):
        cmdline = list()
        cmdline.append("psql")
        if len(self.config.get('dbname')) > 0:
            cmdline.append("--dbname=" + str(self.config.get('dbname')))
        cmdline.append("--command=" + cmd)
        self.verbose.log(cmdline)
        try:
            subprocess.call(cmdline, stdout=subprocess.DEVNULL)
            out = True
        except:
            self.verbose.warning("Couldn't list function: %r" % func)
            out = False
            
        return out

    def dump(self):
        print("Dumping data from pgdb class")
        #print("\tDBname: " + self.config.get('dbname'))
        #print("\tDBuser: " + self.config.get('dbuser'))
        #print("\tDBpass: " + self.config.get('dbpass'))
        self.list_functions()
        if self.dbshell.closed == 0:
            status = "Open"
        else:
            status = "Closed"
        print("Connection: " + status)
        print("DSN: " + self.dbshell.dsn)
        print("AutoCommit: " + str(self.dbshell.autocommit))
        for i in self.dbshell.notices:
            print("History: " + i.replace('\n', ''))
        
    def drop_db(self, dbname=""):
        if len(dname) == 0:
            dbname = self.config.get('dbname')
        self.shell("DROP DATABASE IF EXISTS" + dname + ';')

    def create_db(self, dbname=""):
        if len(dname) == 0:
            dbname = self.config.get('dbname')
            #self.shell("CREATE DATABASE ' + dbname + ' ENCODING=UTF8 TEMPLATE=template0;')

    def drop_table(self, tbname=""):
        if len(tbname) == 0:
            tbname = db1;
        self.shell("DROP TABLE IF EXISTS" + tbname + ';')

