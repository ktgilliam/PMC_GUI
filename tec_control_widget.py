from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
import numpy as np
import gc
from tec_iface import *
from device_controller import DeviceController

tmp_num_tecs = 132
NUM_BOXES = 2
#NUM_BOXES = 1
NUM_BOARDS = 5

class ControllerRequest(IntEnum):
    NO_REQUESTS = 0
    TOGGLE_CONNECTION_A=1
    TOGGLE_CONNECTION_B=2
    ALL_TO_ZERO=3
    LOAD_FROM_FILE=4
    
class ControllerState(IntEnum):
    INIT=0
    DISCONNECTED=1
    CONNECT_IN_PROGRESS = 2
    CONNECTED=3
    
class TECField(GridLayout):
    tec_no = NumericProperty()
    def __init__(self, tec_no, **kwargs): 
        super().__init__(**kwargs)
        self.tec_no = tec_no
        
class TECFieldHeader(GridLayout):
    pass

class TECFieldList(GridLayout):
    num_tec = NumericProperty()
    
    def __init__(self, **kwargs): 
        super(TECFieldList, self).__init__(**kwargs)
        self.num_tec = tmp_num_tecs
        # layout = self.ids['fields']
        # for ii in range(self.num_tec):
        #     tf = TECField(ii+1)
        #     layout.add_widget(tf)
            
    def createFields(self):
        self.height = self.num_tec * 50 / self.cols
        for ii in range(self.num_tec):
            tf = TECField(tec_no=ii+1, width = (self.parent.width-50)/self.cols)
            self.add_widget(tf)
            
class TECControlWidget(GridLayout):
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        
    def loadList(self):
        list = self.ids['tec_field_list']
        list.createFields()
        a = 5        
            
class TECBoxController(DeviceController):
    
    _instances = []

    # There are two TEC boxes, so the kivy callbacks are going to be static methods which use 
    @staticmethod
    def readConfigsFromBoxes():
        for box in TECBoxController._instances:
           # Ask the teensy for a list of its TECs
           pass 
   
    def setAllToZero():
        for box in TECBoxController._instances:
           pass 
    
    def sendAll():
        for box in TECBoxController._instances:
           pass 
       
    def __init__(self, ctrlWidget, nursery, debugMode = False, **kwargs): 
        super().__init__(ctrlWidget, nursery, debugMode)
        self.ControllerRequestList = deque([])
        self.deviceInterface = TecControllerInterface()
        self.deviceInterface.setDebugMode(debugMode)
        TECBoxController._instances.append(self)
