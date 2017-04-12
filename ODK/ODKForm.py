#!/usr/bin/python3

# 
#   Copyright (C) 2017   Free Software Foundation, Inc.
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

# This is a simple bourne shell script to convert raw OSM data files into
# pretty KML. This way when the KML file is loaded into an offline mapping
# program, all the colors mean something. For example, ski trails and
# bike/hiking trails have difficulty ratings, so this changes the color
# of the trail. For skiing, this matches the colors the resorts use. Same
# for highways. Different types and surfaces have tags signifying what type
# it is.


import os
from lxml import etree


class ODKForm(object):
    """Support for parsing an XLS Form"""
    def __init__(self):
        print("Do Nothing")

    def parse(self, file):
        print("Do Nothing")
        doc = etree.parse(file)

        head = list()
        body = list()
        base = ""
        title = ""
        nodesets = list()
        for docit in doc.getiterator():
            if base == "":
                base = docit.base
                print("BAR: %r" % (docit.tag))
            if docit.prefix == 'h':
                index = docit.tag.find('}') + 1
                if docit.tag[index:] == 'title':
                    title = docit.text
                    # Process the header
                elif docit.tag[index:] == 'head':
                    for elit in docit.getiterator():
                        index = elit.tag.find('}') + 1
                        if elit.tag[index:] == 'text':
                            print("HEADY: %r" % elit)
                            if elit.attrib != "":
                                attr = dict(elit.attrib)
                                print("HEAD: %r" % (attr['id']))
                                head.append(attr['id'])

                # Process the body
                elif docit.tag[index:] == 'body':
                    for elit in docit.getiterator():
                        print("BODY: %r %r" % (elit.tag, elit.text))
                        for ref,datatype in elit.items():
                            print("\tFOOBAR: %r , %r" % (ref, datatype))
                            if datatype == '/data/text':
                                print("TEXT")
                                import pdb; pdb.set_trace()
                                #value = l
                            elif datatype == '/data/numeric':
                                print("NUMBERIC")
                                #value = l
                            elif datatype == '/data/timestamp':
                                print("TIMESTAMP")
                                #value = l
                            elif datatype == '/data/time':
                                print("TIME")
                                #value = l
                            elif datatype[:12] == '/data/select':
                                count = datatype[15:]
                                print("SELECT %r" % count)
                                for select in elit.getiterator():
                                    if type(select.text) == str:
                                        if select.text[0] != '\n':
                                            print("\tSELECT: %r" % (select.text))
                                            #import pdb; pdb.set_trace()
                                            #value = l
                            elif datatype[:12] == '/data/choice':
                                count = datatype[13:]
                                print("CHOICE %r" % count)
                                for choice in elit.getiterator():
                                    if type(choice.text) == str:
                                        if choice.text[0] != '\n':
                                            print("\tCHOICE: %r" % (choice.text))
                                            #import pdb; pdb.set_trace()
                                            #value = l
                            elif datatype == '/data/location':
                                print("LOCATION")
                                #value = l
                            elif datatype == '/data/group':
                                print("GROUP")
                                #value = l

            index = docit.tag.find('}') + 1
            if docit.tag[index:] == 'bind':
                #import pdb; pdb.set_trace()
                node = dict(docit.attrib)
                print("YES: %r" % node)
                nodesets.append(node)

        xmlfile = dict()
        xmlfile['head'] = head
        xmlfile['body'] = body
        xmlfile['base'] = base
        xmlfile['nodesets'] = nodesets

        # print("HEAD: %r" % xmlfile['head'])

        return xmlfile

#
# End of Class definitions
#

file = open("/work/Mapping/ODK/Test.xml")
odkform = ODKForm()
xmlfile = odkform.parse(file)
print("HEAD: %r" % xmlfile['head'])
print("BODY: %r" % xmlfile['body'])
print("BASE: %r" % xmlfile['base'])
# print("NODESETS: %r" % nodesets[2]['type'])

quit()

for i in doc.getiterator():
    if i.prefix == 'h':
        index = i.tag.find('}') + 1
        print("FOO: %r %r %r" % (i.attrib, i.tag[index:], i.text))

    if i.attrib == '/data/name:label':
        print("LABEL: %r" % i.attrib)
    if i.attrib == '/data/name:hint':
        print("HINT: %r" % i.attrib)
    if type(i.tag) == str:
        index = i.tag.find('}') + 1
        print("2: %r %r" % (i.tag[index:], i.text))

# The ElementTree class has these fields:
# .attrib       - A dictionary containing the element's
#                 attributes. The keys are the attribute names, and
#                 each corresponding value is the attribute's value.
# .base         - The base URI from an xml:base attribute that this
#                 element contains or inherits, if any; None
#                 otherwise.
# .prefix       - The namespace prefix of this element, if any, otherwise None.
# .sourceline   - The line number of this element when parsed, if
#                 known, otherwise None.
# .tag          - The element's name.
# .tail         - The text following this element's closing tag, up to
#                 the start tag of the next sibling element. If there
#                 was no text there, this attribute will have the
#                 value None.
# .text         - The text inside the element, up to the start tag of
#                 the first child element. If there was no text there,
#                 this attribute will have the value None.
print(doc)
try:
    el = doc.find('model')
    print(el)
except:
    print("Failed")
