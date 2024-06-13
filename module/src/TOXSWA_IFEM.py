# -*- coding: utf-8 -*-
# NB: As indicated in requirements.txt, the heft package should be installed from github repo
# https://github.com/mbraakhekke/heft.git@relative_imports_fix (use pip install git+https://...)
# The version on PiPy does not work due to incorrect syntax for local imports
import os, shutil, pandas, sys, numpy, datetime as dt, time, util, configparser as cp
import postprocess
from util import writeOutputTable
from Catchment import Catchment
from scheduler import Scheduler
from Toxswa import Toxswa
from io import StringIO

hydrologyMassLoadingsFileBase = '.csv'
experimentRootDirName = 'experiments'

def main(configFile):
    config = cp.ConfigParser()
    config.read(os.path.join(configFile))

    coupler = CMF_TOXSWA_coupler(config)
    coupler()
    coupler.postprocess()
    

class CMF_TOXSWA_coupler(object):
    """
    Class for CMF-TOXSWA coupler.
    """
    
    def __init__(self, config):
        """
        Initializes coupler for all reaches
        """
        self.config = config
        self.experimentName = config['general']['experimentName']
        self.experimentDir = os.path.abspath(os.path.join(experimentRootDirName,self.experimentName))
        self.config['toxswa']['toxswaDir'] = os.path.abspath(self.config['toxswa']['toxswaDir'])

        if not os.path.isdir(self.experimentDir): os.makedirs(self.experimentDir)

        util.createDiagnFile(self.experimentDir)
        
        self.reachTable = pandas.read_csv(os.path.join(self.config['general']['inputDir'],self.config['general']['reachFile']),
                                          comment = "#", header = 0, skiprows = [1], index_col = 0)
        reachSel = config['general']['reachSelection'].split(',')
        if not reachSel[0] == 'all': self.reachTable = self.reachTable.loc[reachSel,]
        nReach = self.reachTable.shape[0]

        # initialize the catchment instance
        self.catchment = Catchment()
        for reachID,reachData in self.reachTable.iterrows():
            self.catchment.addReach(reachID,reachData,hydrologyMassLoadingsFileBase)
        self.catchment.finalize()

        self.catchment.catchmentGraph(colorVals=[int(v) for v in self.catchment.hasDrift.values()],
                                      colorMap = 'Reds', fileName = os.path.join(self.experimentDir,'hasDrift'))

        doReach = [not skip for skip in self.catchment.skip.values()]
        self.catchment.catchmentGraph(colorVals=[int(v) for v in doReach],
                                      colorMap = 'Reds', fileName = os.path.join(self.experimentDir,'doReach'))

    def __call__(self):
        """
        Runs TOXSWA for all reaches
        """
        self.scheduler = Scheduler(int(self.config['general']['nWorker']), Toxswa, self.experimentDir, 
                                   self.config['general'], self.config['toxswa'],self.catchment)
        self.scheduler.init()

        priorityVals = [self.scheduler.priority[r] for r in self.catchment.reachIDs]
        self.catchment.catchmentGraph(colorVals=[1-(float(i)/max(priorityVals)) for i in priorityVals],
                                      fileName = os.path.join(self.experimentDir,'schedulerPriority'))
        tStart = time.perf_counter()
        self.scheduler.start()
        dTime = time.perf_counter() - tStart
        print('Total time: ', dTime)

        util.closeDiagnFile()

    def postprocess(self):
        substName = self.config['toxswa']['substanceNames']
        if self.config.has_option('postprocess','timeRangeMassBalancePlot'):
            timeStepRange = list(map(float,self.config['postprocess']['timeRangeMassBalancePlot'].split(',')))
            postprocess.processCatchmentMassBalance(self.catchment, substName,self.experimentDir, timeStepRange = timeStepRange)
        if self.config.has_option('postprocess','timeRangeConcPlot'):
            timeStepRange = list(map(float,self.config['postprocess']['timeRangeConcPlot'].split(',')))
            stepSize = int(self.config['postprocess']['concPlotStep'])
            postprocess.concMap(self.catchment, self.experimentDir, substName, timeStepRange, stepSize = stepSize, percCutoff = 99)

if __name__ == "__main__":
    configFile = sys.argv[1]
    main(configFile)


