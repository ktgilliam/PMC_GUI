from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty
import numpy as np
# import gc
from tec_iface import *
from device_controller import DeviceController
from enum import IntEnum

import tkinter as tk
from tkinter import filedialog
import csv

tmp_num_tecs = 132
NUM_BOXES = 2
# NUM_BOXES = 1
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
            tf = TECField(tec_no=tec.tecNo, width=(
                self.parent.width-50)/self.cols)
            self.ids['TEC'+str(tec.tecNo)] = tf
            self.add_widget(tf)

    def clearFields(self):
        self.clear_widgets()
    
    def setAllFieldValues(self, value):
        for id in self.ids:
            tf = self.ids[id]
            valField = tf.ids['val_field']
            valField.setValue(value)
            
    def setFieldValue(self, tecNo, value):
        tf = self.ids['TEC'+str(tecNo)]
        valField = tf.ids['val_field']
        # valText = str(value)
        valField.setValue(value)
        labelField = tf.ids['tec_label']
        labelField.color = (1,0,0,1)
    
    def getFieldValue(self, tecNo):
        found = False
        for idx, tec in enumerate(self.ids):
            tecField = self.ids[tec]
            if tecField.tec_no == tecNo:
                valFld = tecField.ids['val_field']
                val = float(valFld.text)
                labelField = tecField.ids['tec_label']
                labelField.color = (1,1,1,1)
                found = True
                break
        if found:
            return val
        else:
            return None
        # for id in self.ids:
        #     tf = self.ids[id]
        #     valField = tf.ids['val_field']
        #     valField.setValue(value)
        #     labelField = tf.ids['tec_label']
        #     labelField.color = (1,0,0,1)
    
class TECControlWidget(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def loadList(self, tecList):
        self.list = self.ids['tec_field_list']
        self.list.clearFields()
        self.list.createFields(tecList)

    def enableCommandButtons(self):
        all2ZeroBtn = self.ids['all_to_zero_btn']
        all2ZeroBtn.disabled = False
        readCsvBtn = self.ids['read_from_csv_btn']
        readCsvBtn.disabled = False
        sendAllBtn = self.ids['send_all_btn']
        sendAllBtn.disabled = False
        
    def fillFieldsWithZeros(self):
        # list = self.ids['tec_field_list']
        self.list.setAllFieldValues(0.0)
        
    def setFieldValue(self, tecNo, val):
        # list = self.ids['tec_field_list']
        self.list.setFieldValue(tecNo, val)
        
    def getFieldValue(self, tecNo):
        # list = self.ids['tec_field_list']
        val = self.list.getFieldValue(tecNo)
        return val
        
class TECBoxController(DeviceController):
    _instances = []
    ControllerRequestList = deque([])
    deviceInterface = None

    def __init__(self, ctrlWidget, nursery, debugMode=False, **kwargs):
        super().__init__(ctrlWidget, nursery, debugMode)
        self.nursery = nursery
        TECBoxController.ControllerRequestList = deque([])
        self.deviceInterface = TecControllerInterface("TECCommand")
        self.deviceInterface.setBoxId(len(TECBoxController._instances)+1)
        self.deviceInterface.setDebugMode(debugMode)
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
            if box.deviceInterface.tecConfigListChanged.is_set():  # TODO find a better way to do this
                box.controllerWidget.loadList(box.deviceInterface.getTecList())

        await trio.sleep(0)

        if len(TECBoxController.ControllerRequestList) > 0:
            pass

    async def connectionSucceededHandler(self):
        TECBoxController.readConfigsFromBoxes()
        self.controllerWidget.enableCommandButtons()

    def setAllToZero():
        for box in TECBoxController._instances:
            box.nursery.start_soon(box.deviceInterface.sendAllToZeroCommand)
            box.controllerWidget.fillFieldsWithZeros()
            pass

    def startSendAll():
        for box in TECBoxController._instances:
            box.nursery.start_soon(box.sendAll)
            
    async def sendAll(self):
        list = self.deviceInterface.getTecList()
        for tec in list:
            val = self.controllerWidget.getFieldValue(tec.tecNo)
            if val is not None:
                await self.deviceInterface.sendTecCommand(tec.tecNo, val)
                print("send: " + str(val))
            pass
    
    
    def readCsv():
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV File", ".csv")])
        print(file_path)
        try:
            with open(file_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                tec_cmds = []
                headerRow = True
                for row in spamreader:
                    if headerRow:
                        headerRow = False
                        continue
                    tec_no = int(row[0])
                    tec_cmd = float(row[1])
                    tec_cmd = (tec_no, tec_cmd)
                    tec_cmds.append(tec_cmd)
                    print(', '.join(row))
        except FileNotFoundError:
            return
        
        for box in TECBoxController._instances:
            list = box.deviceInterface.getTecList()
            for tec in list:
                found = False
                for idx, cmd in enumerate(tec_cmds):
                    if cmd[0] == tec.tecNo:
                        print("set tec: " + str(tec.tecNo) + " to " + str(cmd[1]))
                        box.controllerWidget.setFieldValue(tec.tecNo, cmd[1])
                        found = True
                        break
                if found:
                    tec_cmds.pop(idx)
            pass
