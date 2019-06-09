# 
#   Copyright (C) 2017, 2018, 2019   Free Software Foundation, Inc.
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

import logging
import epdb


class kmlfile(object):
    """Output file in KML format."""
    def __init__(self):
        self.file = False

    def open(self, file):
        self.file = open(file, 'w')

    def styles(self, styles):
        file = open(styles, 'r')
        self.write(file.readlines())

    def header(self, title):
        self.title = title
        self.file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.file.write('<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2">\n')
        self.file.write('    <Document>\n')
        self.file.write('        <name>' + title + '</name>\n')
        self.file.write('            <visibility>1</visibility>\n')
        self.file.write('            <open>1</open>\n')

    def write(self, lines):
        if self.file is not False:
            for i in lines:
                self.file.write(i)

    def footer(self):
        if self.file is not False:
            self.file.write('    </Document>\n')
            self.file.write('</kml>\n')
            self.file.close()
            self.file = False
        
    def placemark(self, name="", type="", data="", bound=None):
        self.file.write('        <Placemark>\n')
        if len(name) > 0:
            self.file.write('            <name>' + name + '</name>\n')
        style = '#fixme'
        if type == 'waypoint':
            style = self.wayStyle()
            self.file.write('            ' + str(data))
        elif type == 'line':
            color = self.lineColor()
            style = '#line_' + color
            self.file.write('        <LineString>\n')
            self.file.write('            <tessellate>1</tessellate>\n')
            self.file.write('            <altitudeMode>clampToGround</altitudeMode>\n')
            way = ''
            self.file.write(way + '\n')
            self.file.write('        </LineString>\n')
        elif type == 'polygon':
            style = '#Polygon'
            #self.file.write('            <Polygon>\n')
            self.file.write('                <extrude>1</extrude>\n')
            self.file.write('                <altitudeMode>relativeToGround</altitudeMode>\n')
            #self.file.write('                <' + bound + 'BoundaryIs><LinearRing>\n')
            self.file.write('                ' + data + '\n')
            #self.file.write('                </LinearRing></' + bound + 'BoundaryIs>\n')
            #self.file.write('            </Polygon>\n')
            self.file.write('        <styleUrl>' + style + '</styleUrl>\n')
        elif type == 'multipolygon':
            # We only use the outer bounfaries, as TM can't parse inner
            # boundaries. Actually we don't care about them, as for mapping
            # we don't want to exclude anything.
            #style = '#Polygon'
            self.file.write('            <MultiGeometry>\n')
            #self.file.write('            <outerBoundaryIs><LinearRing>\n')
            epdb.st()
            for poly in data:
                if poly < 0:
                    continue
                print("FIXME: %d" % data[poly].GetX())
                tmp = data[poly].ExportToKML()
                tmp = tmp.replace("<innerBoundaryIs><LinearRing><coordinates></coordinates></LinearRing></innerBoundaryIs>", "")
                print(tmp)
                self.file.write('            ' + tmp + '\n')
            #self.file.write('            </LinearRing></outerBoundaryIs>\n')
            self.file.write('            </MultiGeometry>\n')
        elif type == "multigeometry":
            self.file.write('            <MultiGeometry>\n')

            print("FIXME Count: %r" % data.GetGeometryCount())
            tmp = data.ExportToKML()
            self.file.write('            ' + tmp + '\n')
            #self.file.write('            </LinearRing></' + bound + 'BoundaryIs>\n')
            self.file.write('            </MultiGeometry>\n')
#            self.file.write('        <styleUrl>' + style + '</styleUrl>\n')
        self.file.write('      </Placemark>\n')

    def wayStyle(self):
        logging.warning("Unimplemented")

    def lineColor(self):
        logging.warning("Unimplemented")

    def description(self):
        logging.warning("Unimplemented")
    
    def folderStart(self, folder):
        self.folder = folder
        self.file.write('<Folder>\n')
        self.file.write('<name>' + folder + '</name>\n')
        
    def folderEnd(self):
        self.file.write('</Folder>\n')
        
