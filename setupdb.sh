#!/bin/bash

# 
#   Copyright (C) 2016
#   Free Software Foundation, Inc.
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

name=$1
infile=$2
poly=$3

exists="`psql -l | grep -c ${name}`"
if test "${exists}" -eq 0; then
    #sudo -u postgres psql template1 -c 'create extension hstore;'
    sudo -u postgres createdb -EUTF8 ${name} -T template0
    sudo -u postgres psql ${name} -c 'create extension hstore;'
    sudo -u postgres psql ${name} -c 'create extension postgis;'
fi

filetype="`echo ${infile} | sed -e 's:^.*\.::'`"
osmosis --read-${filetype} file="${infile}" --bounding-polygon file="${poly}"  --write-xml file=${name}.osm
if test $? -gt 0; then
    exit
fi
sudo -u postgres osm2pgsql -v --slim -C 1500 -d ${name} --number-processes 8 ${name}.osm --hstore
if test $? -gt 0; then
    exit
fi
#sudo -u postgres psql -c "GRANT CONNECT on DATABASE ${name} to rob"

