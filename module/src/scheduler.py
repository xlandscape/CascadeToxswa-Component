import time, os, sys, heft, multiprocessing as mp, queue, datetime as dt
from Catchment import Reach
from multiprocessing.managers import SyncManager
from util import writeDiagnOuput, updateDiagnOutput
from collections import OrderedDict as odict

class PriorityQueueManager(SyncManager):
    """
    A custom manager class, derived from SyncManager, meant for sharing a priority queue
    between processes.
    """
    pass
PriorityQueueManager.register("PriorityQueue", queue.PriorityQueue)

class Scheduler(object):
    """
    Scheduler class which creates worker processes and distributes jobs (reach simulations) to them
    using a parallel priority queue. Worker proceses can grab jobs from the queue, with highest 
    priority (lowest value) first, perform the simulation, and send a report back to the scheduler,
    using the report queue. The priority of the reaches is determined based on the catchment topology
    using the HEFT algorithm.
    """

    def __init__(self, nWorker, model, experimentDir, generalConfig, modelConfig, catchment):

        self.nWorker = nWorker
        self.parallel = nWorker > 1
        if self.parallel: 
            self.manager = PriorityQueueManager()
            self.manager.start()
            self.commandQueue = self.manager.PriorityQueue() # queue for sending commends to the workers
            self.reportQueue = mp.Queue() # queue for the workers to report back to the scheduler
        else:
            self.commandQueue = queue.PriorityQueue() # queue for sending commends to the workers
        self.catchment = catchment
        self.model = model
        
        # Figure out the priority of the reaches using the HEFT algorithm.
        # Increase the recursion limit to avoid exceedence by HEFT.
        if sys.getrecursionlimit()<catchment.nReach: sys.setrecursionlimit(catchment.nReach)
        
        if catchment.nReach>1:
            compCostFcn = lambda job, agent: 1
            commCostFcn = lambda ni, nj, A, B: 0
            orders, jobson = heft.schedule(catchment.directedGraph,[0],compCostFcn,commCostFcn)
            self.priority = {evt.job:p for p, evt in enumerate(orders[0])}
        else:
            self.priority = {catchment[0].ID: 1}

        # create the worker processes
        self.workers = []
        for i in range(nWorker):
            
            if self.parallel:
                worker = ParallelWorker(i, model, self.commandQueue, self.reportQueue, experimentDir, generalConfig, modelConfig)
                self.workers.append(mp.Process(target=worker.run))
            else:
                worker = SerialWorker(i, model, self.commandQueue, None, experimentDir, generalConfig, modelConfig)
                self.workers.append(worker)

    def init(self):
        for reach in self.catchment:
            self.commandQueue.put((self.priority[reach.ID],reach.unlink(),'init'))

        if self.parallel:
            # start the workers. They will start immediately with the first reaches
            for worker in self.workers: worker.start()

        nInit = 0
        while nInit < self.catchment.nReach:
            if self.parallel:
                report = self.reportQueue.get()
            else:
                report = self.workers[0].run()
            nInit += 1

    def start(self):
        """
        Starts the simulation.
        """

        # Populate the command queue with the first reaches. 
        for reach in self.catchment.canStartReaches:
            # Set the reach status to running. This will inform the catchment, 
            # which removes the reach from the canstart list
            reach.status = Reach.flagRunning

            # The unlink() function returns a copy of the reach without links to other 
            # reaches or the catchment. This is to avoid exceedence of recursion limit
            # when passing the reach object to the queue.
            self.commandQueue.put((self.priority[reach.ID],reach.unlink(), 'run'))

        # Main execution loop. Keep going until catchment says we're done.
        while not self.catchment.isDone:
            if self.parallel:
                # wait for a worker to report back. This will block execution until 
                # something is in the report queue
                report = self.reportQueue.get()
            else:
                report = self.workers[0].run()

            if report['action'] == 'run':
                for var in report:
                    if var=='reachID': continue
                    updateDiagnOutput(var,report[var])
                writeDiagnOuput(report['reachID'])

            # Inform the reach object of the status. This will signal the catchment 
            # object, which will  figure out which reaches can start next and add 
            # those to the command queue
            if report['status'] in [self.model.flagOk, self.model.flagSkipReach, self.model.flagSkipExist]:
                reach = self.catchment[report['reachID']]
                if reach.status == Reach.flagRunning:
                    reach.status = Reach.flagRunDone
                elif reach.status == Reach.flagCleaning:
                    reach.status = Reach.flagDone

            elif report['status'] == self.model.flagError:
                 self.catchment[report['reachID']].status = Reach.flagError
            
            # If new reaches can start, add them to the command queue
            for reach in self.catchment.canStartReaches:
                reach.status = Reach.flagRunning
                self.commandQueue.put((self.priority[reach.ID],reach.unlink(),'run'))

            for reach in self.catchment.canBeCleanedReaches:
                reach.status = Reach.flagCleaning
                self.commandQueue.put((self.priority[reach.ID],reach.unlink(),'cleanup'))

        if self.parallel:
            # Tell the workers to stop
            for i in range(self.nWorker): self.commandQueue.put((i,'stop'))

            # Wait for the workers to finish
            time.sleep(4)
        
            # terminate the processes
            for worker in self.workers:
                worker.terminate()
    
class Worker:
    """
    Worker class, essentially a shell around the model which instantiates it and 
    grabs reaches from the command queue and starts the model for them.
    """
    def __init__(self, id, model, commandQueue, reportQueue, experimentDir, generalConfig, modelConfig):
        self.id = id
        self.model = model(experimentDir, modelConfig, generalConfig, experimentDir)
        self.commandQueue = commandQueue
        self.reportQueue = reportQueue
        self.idleTime = 0
        self.tStart = None
        self.logFilePath = os.path.join(experimentDir,'worker_'+str(id)+'.log')

class SerialWorker(Worker):
    """
    Serial worker subclass. Simply runs the model 
    """
    def run(self):
        # get a command from the queue. This will block execution until there something in the queue.
        command = self.commandQueue.get()
        priority = command[0]
        reach = command[1]
        action = command[2]
        startTime = dt.datetime.now()
        if action == 'init':
            print('Initializing reach', reach.ID)
            modelReport = self.model.init(reach)
        elif action == 'run':
                print('Running reach', reach.ID)
                modelReport = self.model.run(reach) # run the model. It returns a report with return status and other stuff.
        elif action == 'cleanup':
            print('Cleaning up for reach', reach.ID)
            modelReport = self.model.cleanup(reach)

        statusMsg = self.model.flagMessage[modelReport['status']]
        print('Reach',reach.ID,statusMsg)
        finalReport =  odict.fromkeys(['priority','endTime','startTime'])
        finalReport['priority'] = priority
        finalReport['startTime'] = startTime.strftime('%d-%m-%Y %H:%M:%S')
        finalReport['endTime'] = dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        finalReport['action'] = action
        finalReport.update(modelReport)
        return(finalReport)

class ParallelWorker(Worker):
    """
    Worker class, essentially a shell around the model which instantiates it and 
    grabs reaches from the command queue and starts the model for them.
    """
    def run(self):
        """
        The worker function. Will be called by the scheduler, with worker.start()
        """
        # Execution loop, Keeps going until command "stop" is given.
        print('Worker ', self.id, 'started!')
        self.logFile = open(self.logFilePath,'wt')
        while True:
            # get a command from the queue. This will block execution until there something in the queue.
            tStart = time.perf_counter()
            command = self.commandQueue.get()
            self.idleTime += time.perf_counter() - tStart
            priority = command[0]
            if type(command[1]) is Reach:
                reach = command[1]
                action = command[2]
                startTime = dt.datetime.now()
                if action == 'init':
                    print('worker', self.id, ': initializing reach', reach.ID)
                    self.logFile.write(str(startTime)+': initializing reach'+str(reach.ID)+'\n')
                    modelReport = self.model.init(reach)
                    self.logFile.write(str(dt.datetime.now())+': done initializing reach'+str(reach.ID)+'\n')
                elif action == 'run':
                    print('worker', self.id, ': running reach', reach.ID)
                    self.logFile.write(str(startTime)+': running reach'+str(reach.ID)+'\n')
                    modelReport = self.model.run(reach) # run the model. It returns a report with return status and other stuff.
                    self.logFile.write(str(dt.datetime.now())+': done running reach'+str(reach.ID)+'\n')
                elif action == 'cleanup':
                    print('worker', self.id, ': cleaning up for reach', reach.ID)
                    self.logFile.write(str(startTime)+': cleaning up for reach'+str(reach.ID)+'\n')
                    modelReport = self.model.cleanup(reach) # run the model. It returns a report with return status and other stuff.
                    self.logFile.write(str(dt.datetime.now())+': done cleaning up for reach'+str(reach.ID)+'\n')
                self.logFile.flush()
                statusMsg = self.model.flagMessage[modelReport['status']]
                print('Reach',reach.ID,statusMsg)
                finalReport =  odict.fromkeys(['workerID','priority','endTime','startTime','action'])
                finalReport['workerID'] = self.id
                finalReport['priority'] = priority
                finalReport['startTime'] = startTime.strftime('%d-%m-%Y %H:%M:%S')
                finalReport['endTime'] = dt.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                finalReport['action'] = action
                finalReport.update(modelReport)
                self.reportQueue.put(finalReport)  # put the report in the report queue for the scheduler

            elif command[1] == 'stop':
                self.logFile.close()
                print('worker', self.id, ' stopping. Total wait time:', self.idleTime)
                break
