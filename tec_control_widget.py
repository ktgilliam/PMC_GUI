from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
import numpy as np
# import gc
from tec_iface import *
from device_controller import DeviceController
from enum import IntEnum

tmp_num_tecs = 132
NUM_BOXES = 2
#NUM_BOXES = 1
NUM_BOARDS = 5

class TecControllerRequest(IntEnum):
    NO_REQUESTS = 0
    # POPULATE_LIST = 1
    
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
        # self.num_tec = tmp_num_tecs
        # layout = self.ids['fields']
        # for ii in range(self.num_tec):
        #     tf = TECField(ii+1)
        #     layout.add_widget(tf)
            
    def createFields(self, tecList):
        self.num_tec = len(tecList)
        self.height = self.num_tec * 50 / self.cols
        # for ii in range(self.num_tec):
        #     tf = TECField(tec_no=ii+1, width = (self.parent.width-50)/self.cols)
        #     self.add_widget(tf)
        for tec in tecList:
            tf = TECField(tec_no=tec.tecNo, width = (self.parent.width-50)/self.cols)
            self.ids['TEC'+str(tec.tecNo)] = tf
            self.add_widget(tf)
            
    def clearFields(self):
        self.clear_widgets()
        # for tf in self.children:
        #     pass
        pass
            
class TECControlWidget(GridLayout):
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        
    def loadList(self, tecList):
        list = self.ids['tec_field_list']
        list.clearFields()
        list.createFields(tecList)
        a = 5        


        
class TECBoxController(DeviceController):
    _instances = []
    ControllerRequestList = deque([])
    deviceInterface = None
    
    def __init__(self, ctrlWidget, nursery, debugMode = False, **kwargs): 
        super().__init__(ctrlWidget, nursery, debugMode)
        TECBoxController.ControllerRequestList = deque([])
        TECBoxController.deviceInterface = TecControllerInterface("TECCommand")
        TECBoxController.deviceInterface.setBoxId(len(TECBoxController._instances)+1)
        TECBoxController.deviceInterface.setDebugMode(debugMode)
        TECBoxController._instances.append(self)
        
    # There are two TEC boxes, so the kivy callbacks are going to be static methods which use 
    @staticmethod
    def readConfigsFromBoxes():
        # TECBoxController.ControllerRequestList.append(TecControllerRequest.POPULATE_LIST)
        for box in TECBoxController._instances:
           # Ask the teensy for a list of its TECs
           box.nursery.start_soon(box.deviceInterface.getTecConfigFromTeensy)
           pass 
   
    @staticmethod
    async def connectedStateHandler():
        for box in TECBoxController._instances:
            if box.deviceInterface.tecConfigListChanged.is_set(): #TODO find a better way to do this
                box.controllerWidget.loadList(TECBoxController.deviceInterface.getTecList())
        await trio.sleep(0)
            
        if len(TECBoxController.ControllerRequestList) > 0:
            pass
        
    def setAllToZero():
        for box in TECBoxController._instances:
           pass 
    
    def sendAll():
        for box in TECBoxController._instances:
           pass 
       
