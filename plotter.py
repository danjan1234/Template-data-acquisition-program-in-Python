"""
This module contains a plot class with the capability to plot the streaming data

Author: Justin Duan
Date: 2018-05-22
"""

from multiprocessing import Process, Queue
from matplotlib.ticker import EngFormatter
import matplotlib.pyplot as plt
import numpy as np
import math
import time
import os
        
class Plotter(object):
    """
    This class starts a plot engine that waits the data sent to the queue and 
    plot them out indefinitely

    ============================================================================
    Attributes:
    self.plot: grab the data from the queue and sent them to plot at a 
        specified time interval
    """
    TOGGLE_SAVE = "NO SAVE"
    STOP_FLAG = "STOP"
    NEW_LINE_FLAG = "NEW LINE"
    
    def __init__(self):
        # A multiprocess safe queue used to accept the plotting data from 
        # the main process
        self._queue = Queue()
            
    def plot(self, axesNames=[('x2', 'y1'), ('x2', 'y5'),
                               ('x2', 'y2'), ('x2', 'y3')],
                    labelNames = ['x1', 'x1', 'x1', 'x1'],
                    axisRange=(-1e-9, 1e-9, -1e-9, 1e-9), 
                    engineeringFormat=True, figSize=(10,6), ncols=None,
                    markersize=5, plotLabelFormat=".0f", updateInterval=0.1,
                    saveFigPath=None, keepFig=False, saveFlag=True):
        """
        Wait the data sent to queue and send them to plot at a certain time
        interval
        
        ------------------------------------------------------------------------
        Arguments:
            axesNames: a list of tuples. A list of axes names for all subplots
            labelNames: a list of strings. 
                A list of variables used to label each subplot
            axisRange: tuple, default=(-1e-9, 1e-9, -1e-9, 1e-9)
                The default ranges for x- and y- axes
            engineeringFormat: bool, default=true
                Whether or not the engineering format should be used for the 
                axes lables
            figSize: tuple (width, height). Figure size
            ncols: int, default=None.
                number of columns of the plots. If None, this parameters will
                be automatically determined
            markersize: int, default=5. Plot marker size
            plotLabelFormat: string. 
                A format string used to control the plot label on display
            updateInterval: float, default=0.1.
                This parameter determines how often the figure shold be updated
            saveFigPath: path string, default=None.
                The path to save the figure. If None, then no figure will be
                saved
            keepFig: bool, defualt=False.
                Determine whether or not the figure window should be open or not
            saveFlag: bool, default=True.
                This parameter determine whether or not the figure should be
                saved
        """
        
        # Miscellaneous controls
        self._axesNames = axesNames
        self._labelNames = labelNames
        if self._labelNames is None:
            self._labelNames = [None] * len(self._axesNames)
        self._style = self._styleGen()
        self._markersize = markersize
        self._plotLabelFormat = plotLabelFormat
        self._saveFlag = saveFlag
        
        # Create plots
        if ncols is None:
            ncols = 1
            while ncols * ncols < len(axesNames):
                ncols += 1
        nrows = nrows=len(axesNames) // ncols
        if ncols * nrows == len(axesNames):
            self._fig, self._axes = plt.subplots(nrows, ncols)
        else:
            self._fig, self._axes = plt.subplots(nrows + 1, ncols)
        if hasattr(self._axes, '__iter__'):
            self._axes = self._axes.flatten()
        else:
            self._axes = [self._axes]
        
        # Set figure size
        self._fig.set_size_inches(*figSize)

        # Label the axes
        for ax, (xAxis, yAxis) in zip(self._axes, self._axesNames):
            ax.set_xlabel(xAxis)
            ax.set_ylabel(yAxis)
            ax.set_title(yAxis + ' vs. ' + xAxis, fontsize=14)
            ax.grid()
            ax.set_xlim(axisRange[0], axisRange[1])
            ax.set_ylim(axisRange[2], axisRange[3])
            if engineeringFormat:
                formatter = EngFormatter()
                ax.xaxis.set_major_formatter(formatter)
                ax.yaxis.set_major_formatter(formatter)
          
        plt.tight_layout()
        self._initialPlotting = True
        
        # Show the figure
        plt.show(block=False)
        plt.draw()
        
        # Change window title
        if saveFigPath is not None:
            folderPath, title = os.path.split(saveFigPath)
            if not os.path.exists(folderPath):
                os.makedirs(folderPath)
            self._fig.canvas.set_window_title(title)
        
        # Keep plotting the queue
        self._plotQueue(updateInterval)
        
        if saveFigPath is not None and self._saveFlag:
            folderPath, title = os.path.split(saveFigPath)
            if os.path.exists(folderPath):
                plt.savefig(fname=saveFigPath)
        
        if keepFig:
            plt.show(block=True)
        
    def _styleGen(self):
        """
        A infinite generator that produces various plot styles
        """
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        markers = [".", "o", "v", "^", "<", ">", "1", "2", "3", 
                    "4", "8", "s", "p", "P", "*", "h", "H", "+", 
                    "x", "X", "D", "d", "|", "_"]
        
        i, j = 0, 0
        while True:
            i %= len(colors)
            j %= len(markers)
            yield colors[i] + markers[j]
            i += 1
            j += 1
    
    def _newLine(self, ax, style, label):
        """
        Add a new line to the specific axes. Note the old lines are still 
        preserved
        """
        if label is not None:
            line, = ax.plot([], [], style, markersize=self._markersize, label=label)
            ax.legend(loc='best')
        else:
            line, = ax.plot([], [], style, markersize=self._markersize)
        return line
        
    def _updateSingleAxis(self, ax, x, y):
        """
        Add new data points to the current line of the specific axis
        """
        # Define extra margin and scale extender
        extra_margin = 1e-9
        scale_ext = 1.2
        
        # Set data
        line = ax.get_lines()[-1]
        x_arr, y_arr = line.get_data()
        x_arr = np.append(x_arr, x)
        y_arr = np.append(y_arr, y)
        line.set_data(x_arr, y_arr)

        # Adjust plot ranges
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        max_x = max(x) if hasattr(x, '__iter__') else x
        min_x = min(x) if hasattr(x, '__iter__') else x
        max_y = max(y) if hasattr(y, '__iter__') else y
        min_y = min(y) if hasattr(y, '__iter__') else y
        
        # Automatically adjust the plotting range at the beginning of plotting         
        if self._initialPlotting:
            ax.set_xlim(min_x - extra_margin, max_x + extra_margin)
            ax.set_ylim(min_y - extra_margin, max_y + extra_margin)
            return
            
        if max_x > xmax:
            xmax = max(xmax, (max_x + min_x) / 2 + (max_x - min_x) / 2 * scale_ext)
            ax.set_xlim(xmin, xmax)
        if min_x < xmin:
            xmin = min(xmin, (max_x + min_x) / 2 - (max_x - min_x) / 2 * scale_ext)
            ax.set_xlim(xmin, xmax)
        if max_y > ymax:
            ymax = max(ymax, (max_y + min_y) / 2 + (max_y - min_y) / 2 * scale_ext)
            ax.set_ylim(ymin, ymax)
        if min_y < ymin:
            ymin = min(ymin, (max_y + min_y) / 2 - (max_y - min_y) / 2 * scale_ext)
            ax.set_ylim(ymin, ymax)
        
    def _plotPoint(self, data, new_line=False):
        """
        Add one data point to all charts in the smart way
        Arguments --
            data:       a dictionary (keys can be lists). Used to smartly 
                        assign the data to corresponding plots
            new_line:   create a new line or not
        """
          
        # Plot each axis
        if new_line:
            style = next(self._style)
            
        for i, (ax, (xAxis, yAxis), labelName) in enumerate(zip(
                                self._axes, self._axesNames, self._labelNames)):
            if new_line:
                if labelName is None:
                    label = None
                else:
                    if not isinstance(labelName, list) and not isinstance(labelName, tuple):
                        labelVal = self._getLabelVal(data[labelName])
                        label = labelName + '=' + labelVal
                    else:
                        labelVal = [self._getLabelVal(data[x]) for x in labelName]
                        label = [x + '=' + y for x, y in zip(labelName, labelVal)]
                        label = ", ".join(label)
                self._newLine(ax, style, label)
            self._updateSingleAxis(ax, data[xAxis], data[yAxis])
             
        plt.draw()
        self._fig.canvas.flush_events()
        
        self._initialPlotting = False
    
    def _getLabelVal(self, labelVal):
        if not hasattr(labelVal, '__iter__'):
            return labelVal
        if len(labelVal) == 1:
            labelVal = labelVal[0]
        else:
            labelValMax, labelValMin = max(labelVal), min(labelVal)
            if labelValMax == labelValMin:
                labelVal = labelValMin
            else:
                if len(labelVal) > 5:
                    labelVal = "{}~{}".format(labelValMin, labelMax)
        return format(labelVal,  self._plotLabelFormat)
    
    def _plotQueue(self, updateInterval):
        """
        Keep on plotting
        """    
        continuePlotting = True
        while continuePlotting:
            self._buf = dict()            
            while self._queue.qsize() > 0:
                data = self._queue.get()
                if data == self.STOP_FLAG:
                    continuePlotting = False
                    continue
                if data == self.TOGGLE_SAVE:
                    self._saveFlag = not self._saveFlag
                    continue
                # In case a new line is requested, plot the buffer first
                if self.NEW_LINE_FLAG in data:
                    self._plotBuffer()
                    self._plotPoint(data, new_line=True)
                    continue
                self._fillBuffer(data)
            self._plotBuffer()
            
            time.sleep(updateInterval)
    
    def _fillBuffer(self, data):
        if len(self._buf) == 0:
            self._createBufferEntries(data)
        for key, val in data.items():
            self._buf[key] = np.append(self._buf[key], val)

    def _createBufferEntries(self, data):
        if len(self._buf) > 0:
            return
        for key in data:
            self._buf[key] = np.array([])
            
    def _plotBuffer(self):
        if len(self._buf) > 0:
            self._plotPoint(self._buf, new_line=False)
            self._buf = dict()
        else:
            # Flush GUI event in case there's nothing to do
            self._fig.canvas.flush_events()
            
    def addPoints(self, data):
        """
        Add data points to the queue
        """
        self._queue.put(data)
    
    @classmethod
    def selfTest(cls, pause=0.1):
        """
        Perform the self-test using another process
        """
        def _dummyDataGen(x1, counts=100):
            """
            Dummy data generator used for self test
            The return value is in the form of a dictionary
            """
       
            while counts > 0:
                x2 = counts * 36
                yield {     
                            'x1': x1, 
                            'x2': x2, 
                            'y1': math.sin(x2 / 360 * math.pi) + x1 / 1000,
                            'y2': math.cos(x2 / 360 * math.pi) + x1 / 1000,
                            'y3': math.radians(x2 / 360 * math.pi) + x1 / 2000,
                        }
                counts -= 1
                
        p = Plotter()
        proc = Process( target=p.plot, 
                        kwargs={'ncols': 2,
                                'axesNames': [('x2', 'y1'), ('x2', 'y2'), ('x2', 'y3')],
                                'labelNames': ['x1', 'x1', 'x1'],
                                'updateInterval': 0.1,
                                'saveFigPath': None,
                                'keepFig': False})
        proc.start()
        
        x1_list = [0, 1000]
        for x1 in x1_list:
            dummy_gen = _dummyDataGen(x1, 40)
            for i, x in enumerate(dummy_gen):
                if i == 0:
                    x[p.NEW_LINE_FLAG] = True
                p.addPoints(x)
                time.sleep(pause)
        p.addPoints(p.STOP_FLAG)
        print("Seft test is done!")

if __name__ == '__main__':
    Plotter.selfTest()