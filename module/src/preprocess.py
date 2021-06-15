import pandas, numpy, util, os

def createHydrologyLoadingsFile(sprayDriftFile,hydrologyFile,reachSel,workDir,hydrologyMassLoadingsFileBase):
    # Creates file with hourly hydrology and mass-loadings for the relevant reaches, 
    # based on seperate input files.
    timeStepLength = 3600
    nValPerReach = 364*24+1
    varRead = ['time','depth','flow'] # which columns to read from hydrology file
    units = ['-','m3.s-1','m','g.m-1']

    # Create a to do list with reaches for which file does not yet exist
    reachTodo = []
    for reachID in reachSel:
        if not os.path.isfile(os.path.join(workDir,reachID + hydrologyMassLoadingsFileBase)):
            reachTodo.append(reachID)
    if len(reachTodo) == 0: return()

    # read spray drift file
    spraydrift = pandas.read_csv(os.path.join(sprayDriftFile),parse_dates=['time'])

    # read header of hydrology file
    hdr = pandas.read_csv(hydrologyFile, nrows=0) # read the header

    reachCnt = 0
    reachTodoCnt = 0

    # list of formatter functions for writing output table
    fmt = [lambda x: x.strftime('%d-%b-%y-%Hh%M'),
           lambda x: "%5.4e" %x,
           lambda x: "%7.5f" %x,
           lambda x: "%5.4e" %x]
    
    with open(hydrologyFile,'rt') as hydFile:
        while True:
            try:
                lines = hydFile.readline()
                reachID = lines.split(',', 1)[0]
                if reachID in reachTodo: # if this reach is in the to do list
                    # get all the data for this reach
                    for i in range(0,nValPerReach-1):
                        lines = lines + hydFile.readline()
                    
                    hydrologyRaw = pandas.read_csv(StringIO(lines), names = list(hdr.columns.values),usecols = varRead, parse_dates = ['time'])
            
                    # fill in hydrology in the output table
                    outputTable = pandas.DataFrame(columns=['Time','QBou','DepWat','LoaDrf'])
                    outputTable.Time = hydrologyRaw.time
                    outputTable.QBou = hydrologyRaw.flow/timeStepLength
                    outputTable.DepWat = hydrologyRaw.depth
                    outputTable.LoaDrf = 0

                    # The last time in the hyd file must be 1 Jan 00:00
                    lastDate = outputTable.Time.iloc[-1]
                    if lastDate != dt.datetime(lastDate.year+1,1,1,0,0):
                        nStepMiss = int((dt.datetime(lastDate.year+1,1,1,0,0) - lastDate).total_seconds()/3600)
                        outputTable = pandas.concat([outputTable,outputTable.iloc[numpy.repeat(outputTable.index[-1],nStepMiss)]])
                        outputTable.Time = list(pandas.date_range(outputTable.Time.iloc[0],dt.datetime(lastDate.year+1,1,1,0,0),freq='H' ))

                    # fill in spray drift in the output table
                    for evt in spraydrift[spraydrift.key==reachID].iterrows():
                        outputTable.loc[outputTable.Time == evt[1].time,'LoaDrf'] = evt[1].rate

                    # write output table to file
                    writeOutputTable(os.path.join(workDir,reachID + hydrologyMassLoadingsFileBase),outputTable,fmt, units)

                    reachTodoCnt = reachTodoCnt + 1
                    if reachTodoCnt == len(reachTodo): break
        
            except: # stop in case of error (e.g. end of file)
                break

def createReachFile(reachInputFile,sprayDriftFile, workDir, reachFileName, reachSel = 'all'):
    # Creates file with info on all reaches
    reachTable = pandas.read_csv(reachInputFile,header = 0, index_col = 0) # reach table
    if not reachSel[0].lower() == 'all':
        reachTable = reachTable.ix[reachSel,:]
    else:
        reachSel = reachTable.index.to_list()
    nReach = reachTable.shape[0]
    
    outputTable = pandas.DataFrame(columns=['RchID','x','y','RchIDDwn','Len','WidWatSys','SloSidWatSys',
                                                'ConSus','CntOmSusSol','Rho','ThetaSat','CntOM','hasDrift'])
    units = ['-','m','m','-','m','m','-','g/m3','g/g','kg/m3','m3/m3','g/g']

    # read spray drift file
    spraydrift = pandas.read_csv(os.path.join(sprayDriftFile),parse_dates=['time'])
    outputTable.hasDrift = [reachId in list(spraydrift.key) for reachId in reachTable.index]
    
    # list of formatter functions for writing output table
    fmt = [lambda x: x,                     # Reach ID
           lambda x: "%12g.5" %x,           # X coordinate of reach
           lambda x: "%12g.5" %x,           # Y coordinate of reach
           lambda x: x,                     # IDs of downstream reaches
           lambda x: "%6.1f" %x,            # Length
           lambda x: "%6.2f" %x,            # Width
           lambda x: "%4.2f" %x,            # Slope of bank
           lambda x: "%5.2f" %x,            # Suspended solids
           lambda x: "%4.2f" %x,            # Organic matter content of suspended solids
           lambda x: "%4.0f" %x,            # Bulk density
           lambda x: "%4.2f" %x,            # Porosity
           lambda x: "%4.2f" %x,            # Organic matter content of sediment
           lambda x: 'yes' if x else 'no'   # has drift
           ]

    outputTable.RchID = reachTable.index
    outputTable.RchIDDwn = reachTable.downstream.to_list()
    outputTable.Len = 100
    outputTable.WidWatSys = reachTable.width.to_list()
    outputTable.SloSidWatSys = reachTable.bankslope.to_list()
    outputTable.ConSus = 11.0
    outputTable.CntOmSusSol = numpy.asarray(reachTable.oc)*1.742
    outputTable.Rho = numpy.asarray(reachTable.dens)*1000
    outputTable.ThetaSat = reachTable.porosity.to_list()
    outputTable.CntOM = numpy.asarray(reachTable.oc)*1.742
    outputTable.x = reachTable.x.to_list()
    outputTable.y = reachTable.y.to_list()
    util.writeOutputTable(os.path.join(workDir,reachFileName),outputTable,fmt,units,)
    
    return(reachSel)
