from ha.restInterface import *
import sys

def resBranch(url, level):
    node = rest.read(url)
    print "    "*(level)+node["name"]
    for attr in node.keys():
        if (attr != "name") and (attr != "resources"):
            print "    "*(level+1)+attr+": "+node[attr].__str__()
    if "resources" in node.keys():
        for resource in node["resources"]:
            resBranch(url+"/"+resource, level+1)
        
if __name__ == "__main__":
    server = sys.argv[1]+":7378"
    rest = HARestInterface("rest", server)
    resBranch("/resources", 0)

