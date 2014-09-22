import syslog

def log(*args):
    message = args[0]+" "
    for arg in args[1:]:
        message += arg.__str__()+" "
#    print message
    syslog.syslog(message)


