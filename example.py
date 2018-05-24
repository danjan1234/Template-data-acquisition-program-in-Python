"""
This simple example is to show how to write a custom acquisition program derived
from Experiment
"""

import numpy as np
from experiment import Experiment


class TestExperiment(Experiment):
    """
    A test experiment class
    """
    def __init__(self):
        x0 = range(3)
        x1 = range(3)
        x2 = np.linspace(-10, 10, 1000)
        self._responses = ['x2_read', 'y1', 'y2']
        self._varibles = ['x0', 'x1', 'x2']
        self._varLists = [x0, x1, x2]
        self._ptsPerMeasure = 1000
        self._skipVarSetIfSame = [True] * len(self._varibles)
        self._parameters = {'p1': 1, 'p2': 2, 'pause': 1}
        self._plotAxes = [['x2', 'y1'], ['y1', 'y2']]
        self._plotLabels = [('x0', 'x1'), ('x0', 'x1')]
        super().__init__(responses=self._responses, varibles=self._varibles, 
                    varLists=self._varLists, ptsPerMeasure=self._ptsPerMeasure, 
                    skipVarSetIfSame=self._skipVarSetIfSame,
                    parameters=self._parameters, plotAxes=self._plotAxes, 
                    plotLabels=self._plotLabels, save=True, 
                    fileName="Test_file.txt", folderName="Test_sample", 
                    basePath="C:\\Test_save_folder")
   
    # Some functions in the parent class needs to be overwritten
    def createLogEntry(self):
        entry = {}
        entry["runID"] = self.getRunID()
        entry["start_time"] = self.getStartTime()
        entry["end_time"] = self.getEndTime()
        entry["completed"] = self.getExperimentStatus()
        entry["test_run"] = "test_run" 
        return entry
        
    def configInstrument(self):
        print("Configure the instrument ... (Base class's configInstrument has been successfully overwritten!)")
   
    def closeInstrument(self):
        print("Close instrument ... (Base class's closeInstrument has been successfully overwritten!)")
    
    # Getters for responses (dependent varibles)
    @property
    def y1(self):
        return np.sin(self._x2 + self._x0) + self._x1 + np.random.random(len(self._x2)) * 0.2
        
    @property
    def y2(self):
        return np.cos(self._x2 + self._x0) + self._x1 + np.random.random(len(self._x2)) * 0.15
    
    @property
    def x2_read(self):
        # Introduce some noise
        return self._x2 + np.random.random(len(self._x2)) * 0.1
    
    # Getters and setters for the parameters
    # Note any parameters that do not have property getters or setters will be
    # treated as instance varibles (such as p1 here)
    @property
    def p2(self):
        return 2.71828
    @p2.setter
    def p2(self, val):
        self._p2 = val
    
    # Getters and setters for independent varibles
    @property
    def x0(self):
        print("Getter of x0 is not used")
    @x0.setter
    def x0(self, val):
        self._x0 = val
       
    @property
    def x1(self):
        print("Getter of x1 is not used")
    @x1.setter
    def x1(self, val):
        self._x1 = val
    
    @property
    def x2(self):
        print("Getter of x2 is not used")
    @x2.setter
    def x2(self, val):
        self._x2 = val
        
if __name__ == '__main__':
    with TestExperiment() as ex:
        ex.run()