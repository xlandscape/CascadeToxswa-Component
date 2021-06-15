import pandas, numpy as np, glob, os, progressbar as pgb, datetime as dt, re
from PyPDF2  import PdfFileMerger
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt

def merge_output(catchment,toxswa,outputDir):
    """
    Writes average concentration of all reaches to a single CSV file
    """
    for reach in catchment:
        print('Merging output for reach ', reach.ID, '...')
        toxswa_output = toxswa.get_all_output(reach)
        toxswa_output.to_csv(os.path.join(outputDir,reach.ID + '.csv'), index = False)

def cpuTimeHistogram(catchment):
    diagnostics = pandas.read_csv(diagnFileName)

def concGraph(catchment,timeStepRange, nPlot = 100):
    conc = pandas.read_csv("ConLiqWatTgtAvg_Dmtr.csv")
    idStart = np.argmin(abs(np.asarray(conc['Time step'])-timeStepRange[0]))
    idEnd = np.argmin(abs(np.asarray(conc['Time step'])-timeStepRange[1]))
    timeSteps = np.linspace(idStart,idEnd,num = min(nPlot,idEnd-idStart), dtype = np.intc)
    concSel = conc.iloc[timeSteps]
    maxConc = concSel.filter(regex='Reach').max().max()
    for idx,step in enumerate(timeSteps):
        colorVals = list(conc.filter(regex='Reach').iloc[step])
        makegraph(catchment, colorVals, range = [0,maxConc], format = 'pdf', fileName = 'conc_' + str(idx))

    graphFiles = glob.glob('conc_*.pdf')
    pdf_merger = PdfFileMerger()
    pdf_merger.setPageLayout('/SinglePage')
    for file in graphFiles:
        pdf_merger.append(file)
    with open('conc.pdf', 'wb') as fileobj:
        pdf_merger.write(fileobj)
    pdf_merger.close()
    for file in graphFiles: os.remove(file)
    for file in glob.glob('conc_*'): os.remove(file)

def concMap(catchment, outputDir, substance, timeStepRange, stepSize = 1, fileName = 'conc.pdf', percCutoff = None):
    print('Creating catchment concentration map...')
    varName = 'ConLiqWatTgtAvg' + '_' + substance
    dirName = os.path.dirname(fileName)
    baseName, format = os.path.splitext(fileName)
    conc = None
    for reach in catchment:
        if conc is None:
            conc = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'),  usecols = ['timestep', 'date_time', varName])
            conc.columns = [reach.ID if x==varName else x for x in list(conc.columns)]
        else:
            conc[reach.ID] = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'),  usecols = [varName])
    idStart = np.argmin(abs(np.asarray(conc['timestep'])-timeStepRange[0]))
    idEnd = np.argmin(abs(np.asarray(conc['timestep'])-timeStepRange[1]))

    timeSteps = np.arange(idStart,idEnd,step = stepSize, dtype = np.intc)

    concSel = conc.iloc[timeSteps]
    concSel.iloc[:,2:] = concSel.iloc[:,2:]*1000
    if not percCutoff is None:
        maxConc = np.percentile(concSel.iloc[:,2:].values,percCutoff)
    else:
        maxConc = concSel.iloc[:,2:].max().max()
    for idx,step in enumerate(timeSteps):
        colorVals = list(concSel.iloc[idx,2:])
        title = concSel.loc[step,'date_time']
        catchment.catchmentMap(colorVals, valRange =[0, maxConc], 
                               fileName = os.path.join(outputDir, baseName + '_' + '{:03d}'.format(idx)) + format, 
                               title = title, linewidth = 5)
    
    if len(timeSteps)==1: return

    graphFiles = glob.glob(os.path.join(outputDir, baseName + '_*' + format))
    pdf_merger = PdfFileMerger()
    pdf_merger.setPageLayout('/SinglePage')
    for file in graphFiles:
        pdf_merger.append(file)
    with open(os.path.join(outputDir,fileName), 'wb') as fileobj:
        pdf_merger.write(fileobj)
    pdf_merger.close()
    for file in graphFiles: os.remove(file)

def processInputData(varName,config,catchment,dirName):

    startTime = dt.datetime.strptime(config['general']['startDateSim'],'%d-%b-%Y')
    endTime = dt.datetime.strptime(config['general']['endDateSim'],'%d-%b-%Y') + dt.timedelta(hours=23)

    
    outputTable = pandas.read_csv(os.path.join(config['general']['inputDir'],catchment[0].hydrologyMassLoadingsFile),
                                                    header = 0, parse_dates=[0],infer_datetime_format = True,skiprows = [1],
                                                    usecols = ['Time', varName])

    
    filter = ((outputTable.Time>=startTime) & (outputTable.Time<=endTime+dt.timedelta(hours=1)))
    outputTable = outputTable.loc[filter,]
    outputTable.reset_index(drop=True,inplace=True)
    firstRow = filter.idxmax() + 2
    nRow = filter.sum()
    skipRows = lambda x: not(x==0 or (x>=firstRow and (x<=firstRow+nRow)))
    

    if any(outputTable[varName]>0):
        outputTable.columns = ['Time', catchment[0].ID]
    else:
        outputTable.drop(varName, inplace = True, axis = 1)

    for reach in catchment[1:]:
        var = pandas.read_csv(os.path.join(config['general']['inputDir'],reach.hydrologyMassLoadingsFile),
                                           header = 0, skiprows = skipRows, usecols = [varName])
        if var=='LoaDrf': var = var*config.getfloat('toxswa','scaleFacDrift')
        if any(var[varName]>0):
            outputTable[reach.ID] = var

    outputTable.to_csv(os.path.join(dirName,varName+'.csv'), index = False, header = True)

def processCatchmentMassBalance(catchment, substanceName, outputDir, timeStepRange, fileName = 'catchment_massBalance'):
    timeStepOut = 3600

    fluxVars = [var + '_' + substanceName 
                for var in ['MasDrfWatLay',
                            'MasTraWatLay',
                            'MasTraSed',
                            'MasVolWatLay',
                            ]
               ]
    stateVars = [var + '_' + substanceName  for var in ['MasSed','MasWatLay']]

    massBal = None
    for reach in catchment:
        if massBal is None:
            massBal = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'),  usecols = fluxVars + stateVars)
            timeStep = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'),  usecols = ['timestep'])
            dateTime = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'),  usecols = ['date_time'])
        else:
            massBalReach = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'), usecols = fluxVars + stateVars)
            massBal = massBal.add(massBalReach)
    massBal = timeStep.join(dateTime).join(massBal)
    outFlow = None
    outFlowVarName = 'MasDwnWatLay' + '_' + substanceName
    for reach in catchment.ouletReaches:
        if outFlow is None:
            outFlow = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'), usecols = [outFlowVarName])
        else:
            outFlow = outFlow + pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'), usecols = [outFlowVarName])
    massBal[outFlowVarName] = outFlow
    fluxVars.append(outFlowVarName)

    for var in fluxVars:
        massBal[var] = np.cumsum(massBal[var].to_numpy())

    idStart = np.argmin(abs(np.asarray(massBal['timestep'])-timeStepRange[0]))
    idEnd = np.argmin(abs(np.asarray(massBal['timestep'])-timeStepRange[1]))
    
    masBalErrorVarName= 'MasBalErr' + '_' + substanceName
    massBal[masBalErrorVarName] = massBal[fluxVars].sum(axis=1) - massBal[stateVars].sum(axis=1)
    massBal.to_csv(os.path.join(outputDir,fileName+'.csv'),index=False)

    plt.figure(figsize=(12,12))
    for var in fluxVars:
        plot = plt.plot(timeStep['timestep'].iloc[idStart:idEnd],massBal[var].iloc[idStart:idEnd], label = var)

    for var in stateVars:
        plot = plt.plot(timeStep['timestep'].iloc[idStart:idEnd], massBal[var].iloc[idStart:idEnd], label = var, linewidth = 3)
    
    plt.plot(timeStep['timestep'].iloc[idStart:idEnd],  massBal[masBalErrorVarName].iloc[idStart:idEnd], label = 'Mass balance error', linewidth = 3)
    
    plt.gca().legend()
    if not fileName is None: plt.savefig(os.path.join(outputDir,fileName+'.pdf'))

def plotConcHistograms(catchment, outputDir, substance, timePeriod, nBins = None, stepSize = 1, fileName = 'catchment_histogram.pdf', percCutoff = None):
    varName = 'ConLiqWatTgtAvg' + '_' + substance
    dirName = os.path.dirname(fileName)
    baseName, format = os.path.splitext(fileName)
    conc = None
    for reach in catchment:
        if conc is None:
            conc = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'),  
                                   usecols = ['timestep', 'date_time', varName],
                                   parse_dates=['date_time'],infer_datetime_format =True)
            conc.columns = [reach.ID if x==varName else x for x in list(conc.columns)]
        else:
            conc[reach.ID] = pandas.read_csv(os.path.join(outputDir,reach.ID + '.csv'),  usecols = [varName])

    conc_sel = conc.loc[(conc.date_time>=timePeriod[0]) & (conc.date_time<=timePeriod[1]),:]
    reach_mask = (conc_sel[catchment.reachIDs]>0).apply(any).to_list()
    conc_sel = conc_sel.loc[:,reach_mask]
    nReachSel = sum(reach_mask)
    reachID_sel = [col for col in conc_sel.columns if col.startswith('R')]

    safe_log = lambda x: np.log(x) if x > 0 else np.nan

    conc_cutoff = np.percentile(conc_sel.iloc[:,2:].values,99)
    tmp = conc_sel.iloc[:,2:]
    tmp[tmp>conc_cutoff] = np.nan
    conc_sel.iloc[:,2:] = tmp
    #conc_sel.iloc[:,2:] = np.log(conc_sel.iloc[:,2:])
    #conc_sel[conc_sel==-np.inf]=np.nan
    maxConc = np.nanmax(conc_sel[reachID_sel].to_numpy())
    minConc = np.nanmin(conc_sel[reachID_sel].to_numpy())

    plt.close('all')
    #plt.figure(figsize=(12,12))
    bins = np.linspace(minConc,maxConc,50+1)
    bin_mid = bins[0:-1] + np.diff(bins[0:2])
    for i, c in conc_sel.iterrows():
        count, be = np.histogram(c[2:], bins=bins)
        
        #cumulative
        #plt.plot(np.cumsum(count),bin_mid)
        #axes = plt.gca()
        #axes.set_xlim([0,nReachSel])
        #axes.set_ylim([minConc,maxConc])

        plt.plot(bin_mid,count)
        axes = plt.gca()
        axes.set_ylim([0,nReachSel])
        axes.set_xlim([minConc,maxConc])
        
        
        #plt.gcf().set_size_inches(12,12)
        plt.savefig(os.path.join(outputDir,baseName+'_'+str(i)+'.pdf'))
        plt.close()

    graphFiles = glob.glob(os.path.join(outputDir, baseName + '_*' + format))
    pdf_merger = PdfFileMerger()
    pdf_merger.setPageLayout('/SinglePage')
    for file in graphFiles:
        pdf_merger.append(file)
    with open(os.path.join(outputDir,fileName), 'wb') as fileobj:
        pdf_merger.write(fileobj)
    pdf_merger.close()
    for file in graphFiles: os.remove(file)

def extractOutputVar(varName, substName, outputType = 1, omitZeroReaches = False, cutoffQuantile = None,
                     transpose = False, dirName = None, files = None, reachSel = None, dateTimeFormat = None,
                     reachIDs = None, outputFile = None, period = None, conversionFactor = 1):
    """
    Extracts a single output variable from csv output files for different reaches and 
    saves it as a new csv with reach IDs as column headers.
    files may be a list of file names or a string. In the latter case it may be a 
    globbing pattern (e.g. "*.csv") or a single file name. The paths to the files may be 
    supplied with the files variable or in dirName. In the former case, the output csv file
    will be stored in the current working directory.
    outputType has value 1 or 2 and determines the structure of the csv output:
        - 1: nRow x nCol = nTimeStep x nReach
        - 2: nRow x nCol = nTimestep*nReach x 4.
             The first 3 columns hold the time steps, the date-times, and the reach IDs, the 4rd the value
    """
    if files is None: # no file list specified
        # search for csv files in current or specified directory
        files = list(map(os.path.basename,glob.glob(os.path.join('' if dirName is None else dirName,'*.csv'))))
        if 'diagnostics.csv' in files: files.remove('diagnostics.csv')
    elif type(files) is str: # files is string
        if '*' in files: # wildcard
            files = list(map(os.path.basename,glob.glob(os.path.join('' if dirName is None else dirName,files))))
        else: # one file
            files = [files]
      
    # if selected of reach IDs was passed, filter the file list
    if not reachSel is None:
        sel = [False]*len(files)
        for ID in reachSel:
            for idx, file in enumerate(files):
                if (not reachIDs is None and reachIDs[idx]==ID) or (re.findall('[Rr]\d+',os.path.basename(file))[0] == ID):
                    sel[idx] = True
        files = [i for (i, v) in zip(files, sel) if v]

    # if necessary append directory to files
    if not dirName is None:
        files = [os.path.join(dirName,f) for f in files]
    
    outTable = None
    skipIdx = None
    print('Processing', len(files),'files...')
    varSubstName = '_'.join([varName,substName])
    for file in  pgb.progressbar(files):
        reachID = os.path.splitext(os.path.basename(file))[0]
        if outTable is None:
            outTable = pandas.read_csv(file, usecols = ['timestep','date_time',varSubstName], 
                                       parse_dates = ['date_time'], infer_datetime_format = True)
            
            outTable[varSubstName] =  outTable[varSubstName]*conversionFactor
            if not period is None:
                selIdx = (outTable['date_time']>=period[0]) & (outTable['date_time']<=period[1])
                skipIdx = list(np.where(~selIdx)[0]+1)
                outTable = outTable.loc[selIdx,]
                outTable = outTable.reset_index(drop=True)
            
            if outputType==1:
                outTable.columns = ['timestep','date_time',reachID]
            elif outputType==2:
                outTable.insert(0,'ReachID', [reachID]*len(outTable))
                dateTime = outTable['date_time']
                timeStep = outTable['timestep']

            if omitZeroReaches and all(outTable[varSubstName]==0):
                outTable = outTable.iloc[0:0]

        else:
            if outputType==1:
                reachTable = pandas.read_csv(file, usecols = [varSubstName], squeeze = True, skiprows = skipIdx,index_col=False)
                if not (omitZeroReaches and all(reachTable[varSubstName]==0)):
                    outTable[reachID] = reachTable*conversionFactor
                
            elif outputType==2:
                reachTable = pandas.read_csv(file, usecols = [varSubstName], skiprows = skipIdx,index_col=False)
                reachTable = reachTable*conversionFactor
                if not (omitZeroReaches and all(reachTable[varSubstName]==0)):
                    reachTable.insert(0,'date_time', dateTime.values)
                    reachTable.insert(0,'timestep', timeStep.values)
                    reachTable.insert(0,'ReachID', [reachID]*len(reachTable))
                    outTable = outTable.append(reachTable,ignore_index = True)

    if outputType==2: outTable.columns = list(outTable.columns[:3])+['Value']

    if not cutoffQuantile is None:
        testValues = outTable.Value.to_numpy()
        if outputType == 1:
            pass
        elif outputType==2:
            cutoffLow = np.quantile(testValues[testValues>0],cutoffQuantile[0])
            cutoffHigh = np.quantile(testValues[testValues>0],cutoffQuantile[1])
            testValues[testValues<cutoffLow] = 0
            testValues[testValues>cutoffHigh] = cutoffHigh
            outTable.Value = testValues
            reachIDs = list(np.unique(outTable.ReachID))
            for ID in reachIDs:
                idx = outTable.ReachID==ID
                if all(testValues[idx]==0) and omitZeroReaches:
                    outTable.drop(index=outTable.index[idx],inplace=True)
    
    if outputFile is None:
        outputFile = varName + '.csv'
        if not dirName is None:
            outputFile = os.path.join(dirName,outputFile)

    if transpose:
        outTable.T.to_csv(outputFile, index = True, header = False,date_format=dateTimeFormat)
    else:
        outTable.to_csv(outputFile, index = False, header = True,date_format=dateTimeFormat)

