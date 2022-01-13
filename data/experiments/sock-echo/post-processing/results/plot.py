import math
import matplotlib.pyplot as plt
import re

def parseOutputs(outputsFile):
    out = { }
    out["count"] = {}
    out["accuracy"] = {}
    outputs = open(outputsFile)

    experiment = None
    value = None
    count = None
    nFailures = None
    noExps = None
    for outputLine in list(outputs):
        if "logs_exp" in outputLine:
            addOutput(out,experiment,value,nFailures,count,noExps)
            experiment = adaptLabel(outputLine[:-1])
            out["count"][experiment] = []
            out["accuracy"][experiment] = []
            value = None
            count = None
        if outputLine[0] == ">":
            addOutput(out,experiment,value,nFailures,count,noExps)
            logFileInfo = re.match(r'> all-(?P<value>.*).log \((?P<n>.*) failures\)',outputLine)
            value = adaptValue(logFileInfo.group("value"))
            nFailures = int(logFileInfo.group("n"))
            count = 0
            noExps = 0
        if outputLine[0] == "[":
            count += 1
        if "no failure cascade" in outputLine:
            noExps += 1 
    addOutput(out,experiment,value,nFailures,count,noExps)
    outputs.close()

    # sort experiments' lists by experiment value
    for experiment in out["count"]:
        out["count"][experiment].sort(key=lambda pair:pair[0])
    for experiment in out["accuracy"]:
        out["accuracy"][experiment].sort(key=lambda pair:pair[0])

    return out

# function to add an output, if experiment and value are both defined
def addOutput(outputs,experiment,value,nFailures,count,noExps):
    if experiment and value:
        nExplainedFailures = nFailures - noExps
        outputs["count"][experiment].append([value,count/nExplainedFailures])
        accuracy = nExplainedFailures * 100 / nFailures
        outputs["accuracy"][experiment].append([value,accuracy])

# function to parse a csv timeFile
# with lines s.t. "experiment,logFile,elapsedTime,fileSize,timePerMB"
def parseTimes(timesFile):
    times = {}

    # process each csv line separately
    csvTimes = open(timesFile)
    for csvTime in list(csvTimes):
        splittedTime = csvTime.split(",")
        # add "experiment" to "times", if not there already
        experiment = adaptLabel(splittedTime[0])
        if experiment not in times:
            times[experiment] = []
        # add pair [n,timePerMB], where n is the value used in the experiment run 
        # (n excerpted from logFile name)    
        logFile = splittedTime[1]
        logFileInfo = re.match(r'all-(?P<value>.*).log',logFile)
        value = adaptValue(logFileInfo.group("value"))
        millisPerMB = float(splittedTime[4][:-1]) * 1000
        times[experiment].append([value,millisPerMB])
    
    # sort experiments' lists by experiment value
    for experiment in times:
        times[experiment].sort(key=lambda pair:pair[0])

    return times

def adaptLabel(experimentLabel):
    # excerpt label from experiment name
    label = experimentLabel.split("_")[2]
    label = re.sub("([A-Z])"," \g<0>",label).lower()
    # add unit (if needed) based on type of experiment
    if "rate" in label:
        label += " (req/s)"
    elif "probability" in label:
        label += " (%)"
    
    return label

# function to adapt a given "experimentValue" 
# - if load rate (of the form "0.x"), translated to rate of requests/s
# - if probability (of the form "x%"), unchanged
# - if name of root causing service, translated to length of corresponding cascade
def adaptValue(experimentValue):
    try: # case: numeric value
        num = float(experimentValue)
        if num < 1: # case: load rate
            return int(1/num)
        else: # case: percentage
            return num
    except: # case: name of root causing service
        if experimentValue == "frontend":
            return 1
        elif experimentValue == "orders":
            return 2
        elif experimentValue == "shipping":
            return 3
        elif experimentValue == "rabbitMq":
            return 4
    
    # unknown cases
    return None

# function to plot "experiment" list
def plot(pdfName,experiment,xLabel,yLabel,yDelta):
    # excerpt x/y coordinates from list of pairs
    x = []
    y = []
    maxY = -1
    for pair in experiment:
        x.append(pair[0]) 
        yValue = pair[1]
        y.append(yValue)
        if yValue > maxY:
            maxY = yValue
    
    # configure plot 
    axes = plt.gca()
    axes.set_xticks(x)
    axes.set_ylim([0, math.ceil(maxY)+yDelta])
    plt.plot(x,y) 
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)

    # store plot on PDF
    pdfName = xLabel.split(" ")[0] + "_" + pdfName + ".pdf"
    plt.savefig(pdfName)
    plt.clf()


if __name__ == "__main__":
    
    # ----------------
    # plot outputs
    # ----------------
    outputs = parseOutputs("outputs.txt")
    print(outputs)
    print(outputs["count"])
    for o in outputs["count"]:
        plot("count",outputs["count"][o],o,"number of possible explanations",1)
        plot("success_percentage",outputs["accuracy"][o],o,"explained failures (%)",1) # change label into "successfully explained failures"?
    

    # ----------------
    # plot times
    # ----------------
    times = parseTimes("times.csv")
    print(times)
    for t in times:
        plot("time",times[t],t,"time (ms)",10)
