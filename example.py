"""
This simple example is to show how to write a custom acquisition program derived
from Experiment
"""

import numpy as np
import time
from experiment import Experiment


class TestExperiment(Experiment):
    """
    A test experiment class
    """
    def __init__(self, x0=range(3), x1=range(3), x2=np.linspace(-10, 10, 1000), 
                        p1=1, p2=2, pause=0):
        """
        Note:
        x0, x1, x2 are the variables to be swept
        p1, p2 are the parameters that are fixed during the entire experiment
        """
        self._responses = ['x2_read', 'y1', 'y2']
        self._variables = ['x0', 'x1', 'x2']
        self._varLists = [x0, x1, x2]
        self._ptsPerMeasure = 1000
        self._skipVarSetIfSame = [True] * len(self._variables)
        self._parameters = {'p1': p1, 'p2': p2, 'pause': pause}
        self._plotAxes = [['x2', 'y1'], ['y1', 'y2']]
        self._plotLabels = [('x0', 'x1'), ('x0', 'x1')]
        super().__init__(responses=self._responses, variables=self._variables, 
                    varLists=self._varLists, ptsPerMeasure=self._ptsPerMeasure, 
                    skipVarSetIfSame=self._skipVarSetIfSame,
                    parameters=self._parameters, multiThreadReadWrite=True,
                    plotAxes=self._plotAxes, plotLabels=self._plotLabels, save=True, 
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
    
    # Getters for responses (dependent variables)
    @property
    def y1(self):
        time.sleep(1)
        return np.sin(self._x2 + self._x0) + self._x1 + np.random.random(len(self._x2)) * 0.2
        
    @property
    def y2(self):
        time.sleep(1)
        return np.cos(self._x2 + self._x0) + self._x1 + np.random.random(len(self._x2)) * 0.15
    
    @property
    def x2_read(self):
        time.sleep(1)
        # Introduce some noise
        return self._x2 + np.random.random(len(self._x2)) * 0.1
    
    # Getters and setters for the parameters
    # Note any parameters that do not have property getters or setters will be
    # treated as instance variables (such as p1 here)
    @property
    def p2(self):
        return 2.71828
    @p2.setter
    def p2(self, val):
        self._p2 = val
    
    # Getters and setters for independent variables
    @property
    def x0(self):
        print("Getter of x0 is not used")
    @x0.setter
    def x0(self, val):
        time.sleep(1)
        self._x0 = val
       
    @property
    def x1(self):
        print("Getter of x1 is not used")
    @x1.setter
    def x1(self, val):
        time.sleep(1)
        self._x1 = val
    
    @property
    def x2(self):
        print("Getter of x2 is not used")
    @x2.setter
    def x2(self, val):
        time.sleep(1)
        self._x2 = val
        
if __name__ == '__main__':
    print("Example starts ...")
    currTime = time.time()
    with TestExperiment() as ex:
        ex.run()
        print("Total run time is: {:.2f}".format(time.time() - currTime))