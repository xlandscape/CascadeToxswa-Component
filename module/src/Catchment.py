# -*- coding: utf-8 -*-
import os, io, re, subprocess, copy, graphviz as gv, pandas as pd, matplotlib.pyplot as plt, numpy as np
from scipy.interpolate import griddata
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

os.environ['PATH']=os.environ['PATH']+";C:\\Program Files (x86)\\Graphviz2.38\\bin"

class Catchment(object):
    """
    Class for catchment implemented as a linked list
    """
    def __init__(self):
        self.reaches = {}
        self.canStart = {}
        self.canBeCleaned = {}
        self.failed = {}
        self.nReachDone = 0
        self.ouletReaches = []
        self.inletReaches = []
    
    def addReach(self,ID, reachData, hydrologyMassLoadingsFileBase):
        """
        Adds a reach to the catchment. 
        """
        self.reaches[ID] = Reach(ID, reachData, hydrologyMassLoadingsFileBase, self.signalStatusChange)

    def finalize(self):
        """
        Finalize the catchment after all reaches have been added.
        Sets the links between the reaches.
        """
        self.nReach = len(self.reaches)

        # The Directed Acyclic Graph specifying the watershed topology
        # A dict with for each reach a tuple with the downstream reaches
        self.directedGraph = {}

        for reach in self: # for every reach...
            for dId in list(reach.downstreamRef): # loop through downstream reaches
                if not dId in self.reaches.keys():
                    # remove downstream reach if it is not in the catchment (e.g. if catchment is cropped)
                    del(reach.downstreamRef[dId])
                    reach.downstreamIDs.remove(dId)
                else:
                    downstreamReach = self.reaches[dId]
                    reach.set_downstreamRef(downstreamReach) # set reference to downstream reaches for this reach
                    downstreamReach.set_upstreamRef(reach) # set upstream refence to this reach for downstream reaches
                    downstreamReach.upstreamIDs.append(reach.ID)
                    self.directedGraph[reach.ID] = (dId,)
        
        for reach in self:
            # determine the inlet and outlet reaches
            if len(reach.downstreamIDs)==0:
                self.ouletReaches.append(reach)
            if len(reach.upstreamIDs)==0:
                self.inletReaches.append(reach)

        # set the current status of the reaches and whether or not they have loading from upstream
        # checkstatus() and set_hasUpstreamLoading() propagate downward in the catchment so looping
        # over inlet reaches is sufficient
        for reach in self.inletReaches:
            reach.checkStatus()
            reach.set_hasUpstreamLoading()
        
        for reach in self:
            # set flag indicating whether mass outflow (MFU) file  is Needed
            reach.set_massOutflowFileNeeded()

        
    def __iter__(self):
        """
        Returns iterator over reaches
        """
        return(iter(self.reaches.values()))

    @property
    def reachIDs(self):
        """
        Returns list of reach IDs
        """
        return(list(self.reaches.keys()))

    def __getitem__(self,ID):
        """
        Returns reach for specified ID. ID may be a dict key, a index, or a slice
        """
        if isinstance(ID, int):
            return(list(self.reaches.values())[ID])
        elif isinstance(ID,slice):
            return(list(self.reaches.values())[ID])
        else:
            return(self.reaches[ID])

    def __getattr__(self,name):
        """
        Returns a dict for all reaches with reachIDs as keys and attribute 
        name as values. If an attribute accessed that is not a member of Catchment, this
        function is called. This allows reach attribute prop to be accessed as
        catchment.prop, provided that prop is not an attribute of catchement.
        """
        return({reach.ID: getattr(reach,name) for reach in self})

    def signalStatusChange(self,reach):
        """
        Called by reaches to inform the catchment object of a status change.
        This is used to maintain a list of reaches that can start.
        """
        if reach.stat == Reach.flagCanStart:
            self.canStart[reach.ID] = reach
        elif reach.stat == Reach.flagRunning:
            if reach.ID in self.canStart: del self.canStart[reach.ID]
        elif reach.stat == Reach.flagCanBeCleaned:
            self.canBeCleaned[reach.ID] = reach
        elif reach.stat == Reach.flagCleaning:
            del self.canBeCleaned[reach.ID]
        elif reach.stat == Reach.flagDone:
            self.nReachDone += 1
        elif reach.stat in [Reach.flagError,  Reach.flagUpstreamError]:
            if reach.ID in self.canStart: del self.canStart[reach.ID]
            self.failed[reach.ID] = reach

    @property
    def canStartReaches(self):
        return([reach for reach in self.canStart.values()])

    @property
    def canBeCleanedReaches(self):
        return([reach for reach in self.canBeCleaned.values()])

    @property
    def failedList(self):
        return self.failed

    def getReachProp(self, prop, reachIds = None):
        """
        Returns reach property for all, or a selection of reaches
        """
        return([reach.getProperty(prop) for reach in self])

    @property
    def isDone(self):
        return self.nReachDone==len(self.reaches)

    def catchmentMap(self, colorVals = None, valRange = [0,1], fileName = None, title = None, linewidth = 5):
        withnames = False
        #create figure object and color map
        fig = plt.figure(figsize=(12,12))
        ax = fig.add_subplot(111)#, projection="3d")
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        ax.grid(True)
    
        if type(colorVals) == list:
            cmap = ScalarMappable(cmap='jet',norm = Normalize(valRange[0],valRange[1]))
            cmap.set_array(valRange)
            colorFcn = lambda x: '#%02x%02x%02x' % cmap.to_rgba(x,bytes=True)[0:3]
        else:
            cmap = None
            colorVals = [colorVals]*len(self.reaches)
            colorFcn = lambda x: colorVals[0]
        
        # plot reaches
        for index, reach in enumerate(self): 
            for downstream_reach in reach.downstreamRefs:
                ax.plot([reach.x,downstream_reach.x],[reach.y,downstream_reach.y],color=colorFcn(colorVals[index]), linewidth = linewidth) 
                if withnames:
                    x_coord = (reach.x+downstream_reach.x)/2. 
                    y_coord = (reach.y+downstream_reach.y)/2. 
                    ax.text(x_coord,y_coord,reach.key, verticalalignment='bottom', horizontalalignment='right',
                            color=fontcolor, fontsize=fontsize, 
                            bbox=dict(facecolor=color_waterbody, edgecolor='None', boxstyle='round,pad=.2',alpha=.5))
        
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        if not cmap is None: 
            cbar = plt.colorbar(cmap, ax = ax)
            cbar.ax.tick_params(labelsize=15) 
        if not title is None: plt.title(title,fontsize=18)
        if not fileName is None:
            plt.savefig(os.path.join(fileName))
            plt.close()

        
    def catchmentGraph(self, colorVals = None, colorMap = 'jet', range = [0,1], format = 'pdf', fileName = 'graph'):
        # Makes a graph of the reaches and their connections with graphviz.
        dot = gv.Digraph(engine= 'dot')
        dot.attr('graph', nodesep='1',ranksep = '0.005', margin = '0')
        dot.attr('node', margin = '0',fixedsize = 'false', fontsize = '6',width = '0.1',
                height = '0.05', shape = 'box', style = 'filled', penwidth = '0.0')
        dot.attr('edge', arrowsize = '0.2', penwidth = '0.25')

        if not colorVals is None:
            cmap = ScalarMappable(cmap=colorMap,norm = Normalize(range[0],range[1]))
            colorFcn = lambda x: '#%02x%02x%02x' % cmap.to_rgba(x,bytes=True)[0:3]
        else:
            colorFcn = lambda x: None
            colorVals = [0]*self.nReach
        
        for idx, reach in enumerate(self):
            dot.node(reach.ID,label = reach.ID, fillcolor = colorFcn(colorVals[idx])) # add node/reach
            if len(reach.downstreamRef)>0: # add connections to down stream
                dot.edge(reach.ID, list(reach.downstreamRefs)[0].ID, weight = '10')
        try:
            dot.render(filename=fileName, format = format, renderer=None, formatter=None)
        except:
            pass

class Reach(object):
    """
    Class for reach.
    """

    # Status flags
    flagWaiting = 0
    flagCanStart = 1
    flagRunning = 2
    flagRunDone = 3
    flagCanBeCleaned = 4
    flagCleaning = 5
    flagDone = 6
    flagError = 7
    flagUpstreamError = 8

    def __init__(self, ID, reachData, hydrologyMassLoadingsFileBase, signalStatusChange):
        """
        Creats a reach object.
        """
        if not type(reachData.RchIDDwn) is list: reachData.RchIDDwn = [reachData.RchIDDwn]
        self.ID = ID
        self.hydrologyMassLoadingsFile = ID + hydrologyMassLoadingsFileBase
        self.length = reachData.Len
        self.downstreamIDs = reachData.RchIDDwn
        self.upstreamIDs = []
        self.downstreamRef = {ID:None for ID in reachData.RchIDDwn}
        self.upstreamRef = {}
        self.width = reachData.WidWatSys
        self.slope = reachData.SloSidWatSys
        self.suspSolids = reachData.ConSus
        self.omSuspSolids = reachData.CntOmSusSol
        self.bulkDens = reachData.Rho
        self.porosity = reachData.ThetaSat
        self.omSediment = reachData.CntOM
        self.nSegments  = 1
        self.signalStatusChange = signalStatusChange
        self.stat = Reach.flagWaiting
        self.hasDrift = reachData.Expsd
        self.hasUpstreamLoading = False
        self.x = reachData.X
        self.y = reachData.Y
        self.massOutflowFileNeeded = None

    def unlink(self):
        """
        Returns an "unlinked" copy of the reach, with all references to other reaches and the catchment set to None.
        """
        cp = copy.copy(self)
        cp.downstreamRef = None
        cp.upstreamRef = None
        cp.signalStatusChange = None
        return(cp)

    def set_downstreamRef(self,reach):
        """
        Sets the reference to a single downstream reach.
        """
        if self.downstreamRef[reach.ID] is None: self.downstreamRef[reach.ID] = reach

    def set_upstreamRef(self,reach):
        """
        Sets the reference to a single upstream reach.
        """
        if not reach.ID in self.upstreamRef.keys(): self.upstreamRef[reach.ID] = reach

    @property
    def status(self):
        """
        Returns the status of this reach.
        If the status waiting, it will be updated first, by checking the upstream reaches.
        NB: this function has the property decorator, meaning that if the reach status is 
        accessed as reach.status, this function will be called.
        """
        if self.stat == Reach.flagWaiting: self.checkStatus()
        return(self.stat)

    @status.setter
    def status(self, status):
        """
        Sets status of this reach.
        If the status is done, the downstream reaches will be asked to update their status as well.
        If the status is (upstream)error: all downstream reaches will get upstream error.
        NB: this function has the setter decorator, meaning that if a reach status is set using 
        reach.status = status, this function will be called.
        """
        self.stat = status
        if not self.signalStatusChange is None: self.signalStatusChange(self)
        if status in [Reach.flagError, Reach.flagUpstreamError]:
            for reach in self.downstreamRefs: reach.status = Reach.flagUpstreamError
        elif status == Reach.flagRunDone:
            for reach in self.downstreamRefs: reach.checkStatus()
            for reach in self.upstreamRefs: reach.checkStatus()
            self.checkStatus()
    
    @property
    def upstreamRefs(self):
        """
        Returns iterator over upstream reaches
        """
        return(iter(self.upstreamRef.values()))

    @property
    def downstreamRefs(self):
        """
        Returns iterator over downstream reaches
        """
        return(iter(self.downstreamRef.values()))

    @property
    def skip(self):
        return(not(self.hasUpstreamLoading or self.hasDrift))

    def waterResidenceTime(self,waterDepth,flowRate):
        return self.waterVolume(waterDepth)/flowRate

    def waterVolume(self,waterDepth):
        return self.waterCrossSectionArea(waterDepth)*self.length

    def waterCrossSectionArea(self,waterDepth):
        return waterDepth*(self.width + waterDepth*self.slope)

    def checkStatus(self):
        """
        Checks status for this reach, by looking at the upstream and downstream reaches.
        If the current status is runDone and all downstream reaches are runDone as well, the status
        is set to canBeCleaned.       
        If the status is all upstream reaches have status runDone or done, this reach will get status canStart.
        If any of the upstream reaches has status (upstream)error this reach will get status upstreamError
        """

        if self.stat == Reach.flagRunDone:
            if not self.downstreamRefs or all([reach.status in [Reach.flagRunDone, Reach.flagDone] for reach in self.downstreamRefs]):
                self.status = Reach.flagCanBeCleaned
        elif self.stat == Reach.flagWaiting:
            if not self.upstreamRef or all([reach.status in [Reach.flagRunDone, Reach.flagDone] for reach in self.upstreamRefs]):
                self.status = Reach.flagCanStart
        elif any([reach.status in [Reach.flagError, Reach.flagUpstreamError] for reach in self.upstreamRefs]):
            self.status = Reach.flagUpstreamError

    def set_hasUpstreamLoading(self,flag = False):
        self.hasUpstreamLoading = flag or self.hasUpstreamLoading
        for reach in self.downstreamRefs:
            reach.set_hasUpstreamLoading(self.hasUpstreamLoading or self.hasDrift)

    def set_massOutflowFileNeeded(self):
        self.massOutflowFileNeeded = any([not reach.skip for reach in self.downstreamRefs])