"""
A few assistant classes

Author: Justin Duan
Date: 2018-05-22
"""

import time
import constants
import datetime
import os
from pynput.keyboard import Listener
from threading import Lock

_logFileName = constants.FILE_IO.logFileName

class KeyboardListener(object):
    """
    A keyboard event listener. The keyboard event is used to control the 
    program behavior such as stop, pause, toggle save
    """
    def __init__(self, lock=Lock(), plotterObj=None, saveFlag=True):
        self.stopFlag = False
        self.pauseFlag= False
        self.saveFlag = saveFlag
        self._lock = lock
        self._plotter = plotterObj
        
        self._keyboardListener = Listener(on_release=self._onRelease)
        self._keyboardListener.daemon = True
        self._keyboardListener.start()
        print("At any time, press {} to stop, {} to toggle save, {} for pause".format(
                    constants.FLOW_CTRL.stopKey.name.capitalize(),
                    constants.FLOW_CTRL.toggleSaveKey.name.capitalize(),
                     constants.FLOW_CTRL.togglePauseKey.name.capitalize()))
    
    def _onRelease(self, key):
        """
        Keyboard release event callback function
        """
        with self._lock:
            if key == constants.FLOW_CTRL.togglePauseKey:
                self.pauseFlag = not self.pauseFlag  
                if self.pauseFlag:
                    print("Program paused!")
                else:
                    print("Program resumed!")
            elif key == constants.FLOW_CTRL.stopKey:
                print("Stop requested ...")
                if self._plotter is not None:
                    self._plotter.addPoints(self._plotter.STOP_FLAG)
                self.stopFlag = True
                return False
            elif key == constants.FLOW_CTRL.toggleSaveKey:
                self.saveFlag = not self.saveFlag
                if self._plotter is not None:
                    self._plotter.addPoints(self._plotter.TOGGLE_SAVE)
                print("Save flag is toggled to: {}".format(self.saveFlag))

class FileIO(object):
    """
    A class that deals with file name, file IOs, and a variety of other trivial 
    stuff
    """
    def __init__(self, fileName, folderName, basePath):
        self.markStartTime()
        self.runID = self.generateRunID(self.startTime)
        self.fileName = fileName
        self.fileName = self.runID + '_' + self.fileName
        self.folderName = folderName
        self.basePath = basePath
    
        # Prepare the data folder and file pathes
        self.folderPath = os.path.join(self.basePath, self.folderName)
        self.filePath = os.path.join(self.folderPath, self.fileName)
    
    def markStartTime(self):
        self.startTime = datetime.datetime.now()
    
    def markEndTime(self):
        self.endTime = datetime.datetime.now()
    
    def generateHeader(self, header, columnNames):
        rlt = []
        for key, val in header.items():
            rlt.append("# {} = {}".format(key, val))

        # Column names are included for convenience
        return '\r\n'.join(rlt) + '\r\n\r\n' + '\t'.join(columnNames)
    
    def generateRunID(self, startTime):
        return "{}-{}-{}_{}-{}-{}".format(startTime.year, 
                            startTime.month, startTime.day,
                            startTime.hour, startTime.minute, 
                            startTime.second)
        
    def createLog(self, logFilepath, content):
        # Create the base path folder if it does not exist
        if not os.path.exists(self.basePath):
            os.makedirs(self.basePath)
        with open(logFilepath, mode='x') as f:
            f.writelines('\t'.join(content.keys()) + '\n')
            
    def saveLog(self, content):
        if len(content) == 0:
            return

        logFilepath = os.path.join(self.basePath, _logFileName)
        
        # Create the log file if it does not exist
        if not os.path.exists(logFilepath):
            self.createLog(logFilepath, content)
        
        # Save then new entry to the log file
        rlt = map(str, content.values())
        with open(logFilepath, mode='a') as f:
            f.writelines('\t'.join(rlt) + '\n')