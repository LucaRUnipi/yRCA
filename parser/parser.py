from parser.model.message import MessageType
from parser.templates.chaos_echo import parse # change template for parsing other applications' logs

# The method "parse" imported from the "templates" package must parse a log line and
# return an "Event" object (see "model/event.py")

def parseEvents(eventLogs,targetFile):
    # open source/target files 
    events = open(eventLogs,"r")
    prologFacts = open(targetFile,"w")
    for e in events:
        # parsing log event with chosen template
        event = parse(e)

        # write prolog corresponding fact
        prologFacts.write(logFact(event))

    # close source/target files
    events.close()
    prologFacts.close()

# function for generating the Prolog representation of a log event
# (it takes as input an "Event" -> see module "event.py")
def logFact(event):
    fact = "log("
    fact += event.serviceName + ","
    fact += event.instanceId + ","
    fact += str(event.timestamp) + "," 
    fact += generateMessage(event.message) + ","
    fact += event.severity
    fact += ").\n"
    return fact

# support function for generating a Prolog representation of log messages
# (it takes as input a "Message" -> see module "message.py")
def generateMessage(msg):
    if msg.type == MessageType.CLIENT_SEND:
        return "sendTo(" + msg.parameters.service + ",'" + msg.parameters.requestId + "')"
    if msg.type == MessageType.CLIENT_RECEIVE:
        return "answerFrom(" + msg.parameters.service + ",'" + msg.parameters.requestId + "')"
    if msg.type == MessageType.SERVER_RECEIVE:
        return "received('" + msg.parameters.requestId + "')"
    if msg.type == MessageType.SERVER_SEND:
        return "answeredTo('" + msg.parameters.requestId + "')"
    return "other"
