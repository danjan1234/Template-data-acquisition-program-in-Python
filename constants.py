"""
This file is ideal for defining some of the global variables such as instrument
VISA names, GPIB addresses, etc
"""

from pynput.keyboard import Key

class FLOW_CTRL(object):
    """
    Define some of the global flow control constants including stop, pause, 
    save etc
    """
    stopKey = Key.f5
    toggleSaveKey = Key.f1
    togglePauseKey = Key.f6
    
class FILE_IO(object):
    """
    Constants for file IO
    """
    basePath = None
    logFileName = "Test Log.txt"   

class DUMMY_INSTRUMENT_DEFAULTS(object):
    dummyVisaName = 'abc::edf'
    parameterA = 1
    parameterB = 2