import os

def writeOutputTable(fileName, outputTable, formatters, units = None, headerLines = None, inclColNames = True):
    # Writes output table to file, including possible additional header lines and a units line
    
    outList = []
    tableList = outputTable.to_string(index = False,formatters = formatters, header = inclColNames).split('\n') # Convert to string and split by new line
    tableList = [','.join(line.split()) for line in tableList] # convert spaces to commas
    if not headerLines is None: outList = outList + headerLines # insert top header line, if any
    outList = outList + tableList
    if not units is None: outList.insert(1 + (not outList is None),','.join(units)) # insert the second header line
    outString = '\n'.join(outList) # join all lines again with new lines
    outFile = open(fileName,'w')
    outFile.write(outString)
    outFile.close()


diagnFileName = 'diagnostics.csv'
diagnVars = []
diagnVals = {}
headerWritten = False
def createDiagnFile(dir):
    global diagFile
    diagFile = open(os.path.join(dir,diagnFileName),'wt')

def writeDiagnOuput(reachID):
    global diagFile, headerWritten
    if not headerWritten:
        diagFile.write('Reach')
        for var in diagnVars:
            diagFile.write(',')
            diagFile.write(var)
        diagFile.write('\n')
        headerWritten = True

    diagFile.write(reachID)
    for var in diagnVars:
        diagFile.write(',')
        diagFile.write(str(diagnVals[var]))
    diagFile.write('\n')
    diagFile.flush()

def updateDiagnOutput(name,value):
    global diagnVals
    if not name in list(diagnVars): diagnVars.append(name)
    diagnVals[name] = value

def closeDiagnFile():
    global diagFile
    diagFile.close()