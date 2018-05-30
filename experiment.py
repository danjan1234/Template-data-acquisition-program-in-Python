"""
A template experiment class

Author: Justin Duan
Date: 2018-05-22
"""

import constants
import time
import os
import sys
import numpy as np
import pandas as pd
from plotter import Plotter
from utilities import KeyboardListener, FileIO
from pynput.keyboard import Listener
from multiprocessing import Process
from threading import Thread, Lock
from queue import Queue



class Experiment(object):   
    """
    A template class that treats an experiment in the following manner: an
    experiment measures the responds as a function of a list of given variables 
    under a controlled condition defined by parameters:
        responds = f(variable lists, @ fixed parameters)
    
    ============================================================================
    Attributes: 
    self.parameters: parameters to be set
    self.parametersRead: the read version of the parameters
    self.results: the measurement results pandas.DataFrame
    self.pause: pause time between setting the variables and taking the 
        measurement of the responds
    self.getRunID: return the experiment runID. The runID is essentially the 
        experiment starting time-stamp in a different format
    self.getStartTime: return the experiment starting time
    self.getEndTime: return the experiment finishing time
    self.getExperimentStatus: return the experiment status: completed (1) or (0)
    self.measure: take the measurement of the entire variable space
    self.save: save the measurement results together with the parameter settings
    self.run: pipeline of measure then save
    self.createLogEntry: create an entry of the current experiment to be saved 
        in the log file
    self.configInstrument: configuring the instrument. It's supposed to be
        overwritten by the derived classes
    self.closeInstrument: closing the instrument. It's supposed to be 
        overwritten by the derived classes
    """
    
    _figExtention = '.png'
    
    def __init__(self, responses=[], variables=[], varLists=[[]], 
                    skipVarSetIfSame=[], ptsPerMeasure=1, parameters={}, 
                    multiThreadReadWrite=False, plotAxes=[()], 
                    plotLabels=None, plotEngineeringFormat=True,
                    plotFigSize=(10,6), plotUpdateInterval=0.1, plotMarkerSize=3,
                    plotLabelFormat=".0f", keepFig=False, save=True, 
                    fileName="", folderName="", basePath=""):
        """
        ------------------------------------------------------------------------
        Arguments:
        
        responses: list of strings.
            A list of responses (dependent variables) to be measured
        variables: list of strings. 
            A list of variables (independent variables) to be actively swept
        varLists: list of lists or other iterables.
            Each element in varLists cooresponds to one variable
        skipVarSetIfSame: list of bool. 
            This parameter determines the action to adopt when a variable has
            exactly the same value(s) as in the previous iteration. Each element
            cooresponds to one variable. If the element associted with a certain
            variable is set to true, the set-variable step of this variable will
            be skipped if its value has not changed since last iteration. This
            might save some time for set-then-hold variables
        ptsPerMeasure: int, default=1.
            How many points will be generated and measured simultanuously. For
            DAQ application, one might need multiple points to generated and
            measured at once
        parameters: dictionary.
            The parameters that need to be set beforehand during the measurement
        multiThreadReadWrite: bool
            If true, then multiple threads will be created for read/write of
            parameters, variables, and responses. Note most instrument read/write
            are IO bound. Turning this option on allows for concurrent read/write
            of multiple instrument. This option is still experimental. It's not 
            guaranteed to work all the time
        plotAxes: list of tuples.
            The response-variable pairs to be plotted
        plotLabels: list of strings.
            This parameter determines which dependent/independent variable will
            be used as the label of each subplot
        plotEngineeringFormat: bool, default=True.
            Use engineering format for the label text
        plotFigSize: tuple. Figure size
        plotUpdateInterval: float. This parameter affects the plot update interval
        plotMarkerSize: int. Plot marker size
        plotLabelFormat: string. 
            A format string used to control the plot label on display
        keepFig: bool, default=False. If true, the figure will be preserved 
            after the acquisition termintes
        save: bool, default=True. Save data
        fileName: string. The file name used for saving the measurement data
        folderName: string. The folder name where the data will be saved
        basePath: string. The base path where the data should be saved
        """
        # Memorize parameters
        self._responses = responses
        self._variables = variables
        self._varLists = varLists
        self._skipVarSetIfSame = skipVarSetIfSame
        self._columns = self._variables + self._responses
        self._ptsPerMeasure = max(1, int(ptsPerMeasure))
        self.parameters = parameters
        self._multiThreadReadWrite = multiThreadReadWrite
        self._plotAxes = plotAxes
        self._plotLabels = plotLabels
        self._plotEngineeringFormat = plotEngineeringFormat
        self._plotFigSize = plotFigSize
        self._plotUpdateInterval = plotUpdateInterval
        self._plotMarkerSize = plotMarkerSize
        self._plotLabelFormat = plotLabelFormat
        self._keepFig = keepFig
        self._fileName = fileName
        self._folderName = folderName
        self._basePath = basePath
        
        # Validate the inputs
        self._validateInputs()
        
        # Set and read parameters
        if 'pause' not in self.parameters:
            self.parameters['pause'] = 0
        self._setParameters()
        self.parametersRead = self._getParameters()
        
        # Initialization
        self._completed = True
        self._preVarArray = None
        self._ptsCount = 0
        if self._skipVarSetIfSame is None or len(self._skipVarSetIfSame) == 0:
            self._skipVarSetIfSame = [False for _ in self._variables]
        
        # Helper instances
        self._keyboardListener = KeyboardListener(None, save)
        self._fileIO = FileIO(fileName=fileName, folderName=folderName,
                            basePath=basePath)
        self._plotter, self._plotterProc = self._createPlotterProc()
        self._keyboardListener._plotter = self._plotter
        if self._multiThreadReadWrite:
            self._createThreads()
            self._lock = Lock()
    
    def getRunID(self):
        return self._fileIO.runID      
        
    def getStartTime(self):
        return self._fileIO.startTime
        
    def getEndTime(self):
        return self._fileIO.endTime
        
    def getExperimentStatus(self):
        return self._completed
        
    def _createPlotterProc(self):
        saveFigPath = None
        if self._keyboardListener.saveFlag:
            saveFigPath = self._fileIO.filePath[:-4] + self._figExtention
        plotter = Plotter()
        proc = Process( target=plotter.plot, 
                        kwargs={'axesNames': self._plotAxes,
                                'labelNames': self._plotLabels,
                                'engineeringFormat': self._plotEngineeringFormat,
                                'figSize': self._plotFigSize,
                                'markersize': self._plotMarkerSize,
                                'plotLabelFormat': self._plotLabelFormat,
                                'updateInterval': self._plotUpdateInterval,
                                'saveFigPath': saveFigPath,
                                'keepFig': self._keepFig
                                } )
        proc.start()
        return plotter, proc
    
    def _validateInputs(self):
        if not os.path.isabs(self._basePath):
            raise Exception("The given base path is not an absolute path")
        if not isinstance(self.parameters, dict):
            raise Exception("The given parameter inputs are not in the form of dictionary")
        if len(self._variables) != len(self._varLists):
            raise Exception("The given variables and their settings are of different lengths")
    
    def _setParameters(self):
        if self._multiThreadReadWrite:
            self._setParametersMultiThread()
        else:
            self._setParametersSingleThread()

    def _setParametersSingleThread(self):
        for key, val in self.parameters.items():
            setattr(self, key, val)
            
    def _setParametersMultiThread(self):
        threads = []
        for key, val in self.parameters.items():
            th = Thread(target=setattr, args=(self, key, val))
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
    
    def _getParameters(self):
        if self._multiThreadReadWrite:
            return self._getParametersMultiThread()
        else:
            return self._getParametersSingleThread()
    
    def _getParametersSingleThread(self):
        parametersRead = {}
        for key in self.parameters:
            parametersRead[key] = getattr(self, key)
        return parametersRead
    
    def _getParametersMultiThread(self):
        threads = []
        parametersRead = {}
        for key in self.parameters:
            def _getattr():
                parametersRead[key] = getattr(self, key)
            th = Thread(target=_getattr)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        return parametersRead
     
    def measure(self):
        """
        Measure the data
        """
        varGridIter = self._varGridIterator()
        
        # self._results: 1st dimention - observations; 2nd dimention - features
        self._results = None
        try:
            while True:
                self._testPause()
                varArray = np.array([next(varGridIter) for _ in range(
                                                    self._ptsPerMeasure)])
                if self._keyboardListener.stopFlag:
                    self._completed = False
                    break
                self._setVaribles(varArray)
                time.sleep(self.pause)
                dataArray = np.concatenate((varArray, self._getResponses()), 
                                            axis=1)
                if self._results is None:
                    self._results = dataArray
                else:
                    self._results = np.concatenate((self._results, dataArray))
                self._updatePlotData(dataArray)
                self._ptsCount += len(varArray)
        except StopIteration:
            pass
        
        # Stop plotting
        while self._plotterProc.is_alive():
            self._plotter.addPoints(self._plotter.STOP_FLAG)
            time.sleep(0.05)
        
        # Create measurement result pandas.DataFrame
        self.results = self._createResultDF()
    
    def _testPause(self):
        pauseFlag = True
        while pauseFlag:
            pauseFlag = self._keyboardListener.pauseFlag & ~self._keyboardListener.stopFlag
            if pauseFlag:        
               time.sleep(0.05)
    
    def _createResultDF(self):
        if self._results is None:
            return
        return pd.DataFrame(self._results, columns=self._columns)
   
    def _createThreads(self):
        # self._threads: variable / response name -> thread, queue
        self._threads = {}
        for variable in self._variables:
            q = Queue()
            th = Thread(target=self._setAttrQueue, args=(variable,), 
                        daemon=True)
            self._threads[variable] = th, q
            th.start()
        for response in self._responses:
            q = Queue()
            th = Thread(target=self._getAttrQueue, args=(response,), 
                        daemon=True)
            self._threads[response] = th, q
            th.start()
            
    def _setVaribles(self, varArray):
        if self._multiThreadReadWrite:
            self._setVariblesMultiThread(varArray)
        else:
            self._setVariblesSingleThread(varArray)
            
    def _setVariblesSingleThread(self, varArray):
        for i, variable in enumerate(self._variables):
            if (self._preVarArray is not None and varArray.shape == 
                                self._preVarArray.shape and np.all(
                                varArray[:, i] == self._preVarArray[:, i]) 
                                and self._skipVarSetIfSame[i]):
                continue
            val = varArray[:, i]
            val = val[0] if len(val) == 1 else val
            setattr(self, variable, val)
        self._preVarArray = varArray
    
    def _setVariblesMultiThread(self, varArray):
        self._alreadySet = 0
        shouldSet = 0
        for i, variable in enumerate(self._variables):
            if (self._preVarArray is not None and varArray.shape == 
                                self._preVarArray.shape and np.all(
                                varArray[:, i] == self._preVarArray[:, i]) 
                                and self._skipVarSetIfSame[i]):
                continue
            val = varArray[:, i]
            val = val[0] if len(val) == 1 else val
            self._threads[variable][1].put(val)
            shouldSet += 1
        # Wait until all variable setters start
        alreadySet = 0
        while True:
            with self._lock:
                alreadySet = self._alreadySet
            if alreadySet == shouldSet:
                break
            time.sleep(0.01)
        self._preVarArray = varArray
        
    def _setAttrQueue(self, variable):
        while True:
            currQueue = self._threads[variable][1]
            if currQueue.qsize() > 0:
                val = currQueue.get()
                setattr(self, variable, val)
                with self._lock:
                    self._alreadySet += 1
            time.sleep(0.01)
                    
    def _getResponses(self):
        if self._multiThreadReadWrite:
            return self._getResponsesMultiThread()
        else:
            return self._getResponsesSingleThread()
                
    def _getResponsesSingleThread(self):
        rlt = []
        for response in self._responses:
            currRlt = getattr(self, response)
            currRlt = [currRlt] if not hasattr(currRlt, '__iter__') else currRlt
            rlt.append(currRlt)
        rltArray = np.array(rlt)
        return rltArray.T
   
    def _getResponsesMultiThread(self):
        self._currRlt = {}
        rlt = []
        for response in self._responses:
            self._threads[response][1].put(True)
        # Wait until all responses to complete data collection
        while len(self._currRlt) < len(self._responses):
            time.sleep(0.01)
        for response in self._responses:
            currRlt = self._currRlt[response]
            currRlt = [currRlt] if not hasattr(currRlt, '__iter__') else currRlt
            rlt.append(currRlt)
        rltArray = np.array(rlt)
        return rltArray.T
        
    def _getAttrQueue(self, response):
        while True:
            currQueue = self._threads[response][1]
            if currQueue.qsize() > 0:
                val = currQueue.get()
                self._currRlt[response] = getattr(self, response)
            time.sleep(0.01)
    
    def _varGridIterator(self):
        """
        Returns a DFS iterator through the variable lists
        """
        return self._varGridIteratorHelper([])
        
    def _varGridIteratorHelper(self, stack):
        if len(stack) == len(self._variables):
            yield list(stack)
            return
        
        for x in self._varLists[len(stack)]:
            stack.append(x)
            yield from self._varGridIteratorHelper(stack)
            stack.pop()
            
    def _updatePlotData(self, dataArray):
        """
        Update the plot data
        
        dataArray: 1st dimention - observations; 2nd dimention - features
        """
        newLineIndices = self._generateNewLineIndices(dataArray)
        for i in range(1, len(newLineIndices)): 
            start = newLineIndices[i - 1]
            end = newLineIndices[i]
            if start == end:
                continue
            plotData = {}
            if i >= 2:
                plotData[self._plotter.NEW_LINE_FLAG] = True
            for colIdx, col in enumerate(self._columns):
                plotData[col] = dataArray[start:end, colIdx]
            self._plotter.addPoints(plotData)
    
    def _generateNewLineIndices(self, dataArray):
        """
        Generate the index on dataArray where a new line must be added to 
        the plot
        """
        tmp = len(self._varLists[-1])
        start = self._ptsCount // tmp 
        if self._ptsCount % tmp != 0:
            start += 1
        end = (self._ptsCount + len(dataArray)) // tmp
        if (self._ptsCount + len(dataArray)) % tmp == 0:
            end -= 1
        return [0] + [x * tmp - self._ptsCount for x in range(start, end + 1)
                                                ] + [len(dataArray)]
    
    def run(self):
        """
        Pipeline of measure and save steps
        """
        self.measure()
        self.save()
    
    def save(self):
        """
        Save the log file and the measured data as text files
        """
        if self._keyboardListener.saveFlag:
            print("Save data ...")
            self._fileIO.markEndTime()
            self._saveLog()
            self._saveData()
        
    def _saveLog(self):
        entry = self.createLogEntry()
        self._fileIO.saveLog(entry)
        
    def _saveData(self):
        # Create the data folder if it does not exist
        if not os.path.exists(self._fileIO.folderPath):
            os.makedirs(self._fileIO.folderPath)
            
        np.savetxt(self._fileIO.filePath, self._results, fmt='%.6g', 
                delimiter='\t', header=self._generateHeader(), comments='', 
                newline='\r\n')
    
    def _generateHeader(self):
        """
        Concatenated the set and read parameters into a single header string of
        the data file to save
        """
        header = {}
        for parameter, value in self.parameters.items():
            header[parameter] = str(value)
        for parameter, value in self.parametersRead.items():
            if value == self.parameters[parameter]:
                continue
            header[parameter + ' (Read)'] = str(value)
         
        header['completed'] = self._completed
 
        return self._fileIO.generateHeader(header, self._columns)
        
    def __enter__(self):
        self.configInstrument()
        return self
    
    def __exit__(self, *args):
        self.closeInstrument()
        # The following is unpleasant. However, if ptsPerMeasure is large, the
        # following is the only guaranteed way to terminate the program
        os._exit(1)
    
    def createLogEntry(self):
        """
        Create the entry of the log file. This function is supposed to be 
        overwritten by the derived class. If there is nothing to log, return 
        {}, which will skip the logging step
        
        Return: a dictionary
        """
        print("Warning: the base class's createLogEntry function is supposed to be overwritten")
        return {}
    
    def configInstrument(self):
        """
        Configure the instrument in the proper way. This function is supposed 
        to be overwritten by the derived class
        """
        assert False, "Error: the base class's configInstrument function is supposed to be overwritten"
   
    def closeInstrument(self):
        """
        Close, restore, or reset the instrument in the proper way. This 
        function is supposed to be overwritten by the derived class
        """
        assert False, "Error: the base class's closeInstrument function is supposed to be overwritten"
        
if __name__ == '__main__':
    with TestExperiment() as ex:
        ex.run()