#!/usr/bin/python3

import osmium
import shapely.wkb as wkblib

# A global factory that creates WKB from a osmium geometry
wkbfab = osmium.geom.WKBFactory()


class OSMWriter(osmium.SimpleHandler):
    def __init__(self, writer):
        osmium.SimpleHandler.__init__(self)
        self.writer = writer

    def node(self, n):
        self.writer.add_node(n)

    def way(self, n):
        self.writer.add_way(n)

    def relation(self, n):
        self.writer.add_relation(n)


class CounterHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.num_nodes = 0
        self.num_ways = 0
        self.num_rels = 0
        self.num_addrs = 0

    def node(self, n):
        self.num_nodes += 1
        
    def way(self, n):
        self.num_ways += 1
        
    def relation(self, n):
        self.num_rels += 1

    def count_addresses(self, tags):
        if tags['addr:housenumber'] is not None:
            self.num_addrs += 1

if __name__ == '__main__':
    h = CounterHandler()
    h.apply_file("interpreter.osm")
    print("Number of nodes: %d" % h.num_nodes)
    print("Number of ways: %d" % h.num_ways)
    print("Number of relations: %d" % h.num_rels)
    print("Number of addresses: %d" % h.num_addrs)

    writer = osmium.SimpleWriter('nodes.osm')
    n = OSMWriter(writer)
    n.apply_file("interpreter.osm")

