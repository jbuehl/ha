#!/usr/bin/env python
# Print the resources and their attributes that are published in a REST service

import sys
from ha.restInterface import *

# print out the resources in a branch of the tree
def resBranch(path, level):
    node = rest.read(path)
    print "    "*(level)+node["name"]
    # print the resource attributes
    for attr in node.keys():
        if (attr != "name") and (attr != "resources"):
            print "    "*(level+1)+attr+": "+node[attr].__str__()
    # if the resource is a collection, print its resources
    if "resources" in node.keys():
        for resource in node["resources"]:
            resBranch(path+"/"+resource, level+1)
        
if __name__ == "__main__":
    # get the host name
    hostName = sys.argv[1]
    # add the default port if it is not specified
    if len(hostName.split(":")) == 1:
        hostName += ":7378"
    # instantiate the REST client
    rest = RestInterface("rest", service=hostName, cache=False)
    resBranch("/resources", 0)

