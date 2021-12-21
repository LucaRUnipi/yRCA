import os
import re
import sys

# function comparing the explanations generated by "explain.py" with
# with the "realTrace" produced by "post_process.py"
# (returns the index of the explanation corresponding to "realTrace",
# or -1 if there is no corresponding explanation)
def compareOutputs(explanationsPath,realTracePath):
    # creating a string denoting the "realTrace"
    realTraceFile = open(realTracePath, "r")
    trace = ""
    for rtLine in list(realTraceFile):
        trace += rtLine.replace("\n","").replace(" ","")
    realTraceFile.close()

    # creating a list of strings, each corresponding to one of the possible
    # "explanations" found by "explain.py"
    explanationsFile = open(explanationsPath,"r")
    exp = ""
    exps = []
    for expLine in list(explanationsFile):
        expLine = expLine.replace(" ","")
        # if finished parsing explanation, adding it to list of explanations
        if expLine == "\n":
            exps.append(exp)
            exp = ""
        # otherwise, continue parsing explanation
        else:
            # considering only "interaction" events
            if "unreachable" in expLine or "internalerror" in expLine or "neverstarted" in expLine:
                continue
            # removing "[<probability>]", if any
            event = re.sub(r"\[\d+.\d+\]:","",expLine).replace("\n","")
            # adding event to explanation
            exp += event.replace("\n","")
    explanationsFile.close()

    # returning the index of the real trace in the list of found explanations
    try:
        return exps.index(trace)
    # or -1, otherwise
    except:
        return -1

if __name__ == "__main__":
    # output CSV file
    outputFile = "output.csv"
    output = open(outputFile,"w")

    # get absolute path of explainer
    explainer = os.path.abspath("../../../../explain.py")

    # get absolute path of folder with logs
    logFolder = os.path.abspath("../generated-logs")

    # get absolute path of templater
    templates = os.path.abspath("../../../templates/chaos-echo.yml")
    # templates = os.path.abspath("../../../templates/chaos-echo-noid.yml")

    # process log subfolders, separately
    subfolders = os.listdir(logFolder)
    for subfolder in subfolders:
        # get logfiles in subfolder
        logSubfolder = os.path.join(logFolder,subfolder)
        logFiles = os.listdir(logSubfolder)

        # process each log file, separately
        for file in logFiles:
            print("*"*5 + file + "*"*5)
            # create csv string for outputs
            output.write(file)

            # get absolute of log file 
            logFile = os.path.join(logSubfolder,file)
            
            # process each failure event of the frontend, separately
            grepFailures = "grep ERROR " + logFile + " | grep _edgeRouter | grep -v own"
            allFailures = os.popen(grepFailures)
            failures = list(allFailures)[-100:] # considering the last 100 failures
            print("considering " + str(len(failures)) + " failures")
            for failure in failures:
                # generate JSON file containing the failure to explain 
                failureJSON = open("failure","w")
                failureJSON.write(failure)
                failureJSON.close()
                cwd = os.getcwd()
                failureFile = os.path.join(cwd,"failure")

                # process failure file with "explain.py"
                explanations = os.path.join(cwd,"explanations")
                os.chdir("../../../..")
                runExplainer = "python3 explain.py " + failureFile + " " + logFile + " " + templates + " > " + explanations
                os.system(runExplainer)
                os.chdir(cwd)
                
                # process failure file with "print_trace.py"
                realTrace = os.path.join(cwd,"trace") 
                runTracer = "python3 print_trace.py failure " + logFile + " > " + realTrace
                os.system(runTracer)
                
                # compare outputs and store them in CSV file
                expIndex = compareOutputs(explanations,realTrace)
                output.write("," + str(expIndex))
            
            # write csv line on output file
            output.write("\n")
    output.close()