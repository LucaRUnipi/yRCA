from pyswip import Prolog
from explainer.model.explanations import Explanations

def explain(event,appLogs,nSols):
    # create Prolog reasoner
    reasoner = Prolog()
    
    # load knowledge base
    reasoner.consult("explainer/prolog/severity.pl")
    reasoner.consult("explainer/prolog/explain.pl")
    reasoner.consult(appLogs)
    
    # read event to explain
    eventFile = open(event,"r")
    eventToExplain = eventFile.readline() # read line corresponding to event
    eventFile.close()
    eventToExplain = eventToExplain[:len(eventToExplain)-2] # remove "." and "\n" at the end
    
    # run Prolog reasoner to find (and return) root causes
    # query example: findall(C,causedBy(log(frontend,f1,69,other,err),C), L), sort(L,Explanations).
    # rootCauses = list(reasoner.query("findall(C,causedBy(" + eventToExplain + ",C), L), sort(L,Explanations)"))
    # run Prolog reasoner to find "nSols" root causes
    # query example: findnsols(nSols,C,causedBy(log(frontend,f1,69,other,err),C), Explanations).
    rootCauses = list(reasoner.query("findnsols(" + str(nSols) + ",C,causedBy(" + eventToExplain + ",C), Explanations)"))
    return Explanations(rootCauses[0]["Explanations"])