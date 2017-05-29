appConfig = "appConfig.yaml"

import yaml
import threading
import subprocess
from ha import *

# global dictionary of ha objects
objects = {}

# Locate the module containing the definition of the specified class
def findClassDef(className):
    classDef = subprocess.check_output("grep -rl class\ "+className+"\( "+libDir, shell=True)[len(appDir):].rstrip(".py\n").replace("/",".")
    debug("debugAppConfig", className, classDef)
    return classDef
    
# Define an object of the specified class
def defObject(objName, className, args):
    # get the list of class arguments that are object references
    try: exec("objArgs = "+className+".objectArgs")
    except AttributeError: objArgs = []
    # assemble the argument string
    argStr = ""
    for arg in args.keys():
        if arg in objArgs:                                  # arg is an object reference
            if isinstance(args[arg], list):                 # list of object references
                argStr += arg+"=["
                for subArg in args[arg]:
                    argStr += "objects['"+subArg+"'], "
                argStr = argStr[:-2]+"], "
            else:                                           # single object reference
                argStr += arg+"=objects['"+args[arg]+"'], "
        elif isinstance(args[arg], str):                    # arg is a string
            argStr += arg+"='"+args[arg]+"', "
        else:                                               # arg is numeric or other
            argStr += arg+"="+str(args[arg])+", "
    exec("objects['"+objName+"'] = "+className+"(name='"+objName+"', "+argStr[:-2]+")")
    debug("debugAppConfig", objName, className, "("+argStr[:-2]+")")

if __name__ == "__main__":
    # load app config data
    config = yaml.load(file(configDir+appConfig))

    # define global config variables
    for conf in config["config"].keys():
        exec(conf+" = "+str(config["config"][conf]))

    # create state change event and resource lock
    try: exec("objects['"+config["event"]+"'] = threading.Event()")
    except KeyError: pass
    try: exec("objects['"+config["lock"]+"'] = threading.Lock()")
    except KeyError: pass
    
    # create ha objects
    for obj in config["objects"]:
        exec("from "+findClassDef(obj[1])+" import *")
        defObject(obj[0], obj[1], obj[2])

    # start interfaces and servers
    for start in config["start"]:
        objects[start].start()
        
    
