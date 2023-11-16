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
                box.controllerWidget.enable_found_tecs(box.deviceInterface.getTecList())
            pass

        await trio.sleep(0)

        if len(TECBoxController.ControllerRequestList) > 0:
            pass

    async def connectionSucceededHandler(self):
        TECBoxController.readConfigsFromBoxes()
        if hasattr(self.controllerWidget, "enableCommandButtons"):
            self.controllerWidget.enableCommandButtons()

    
    def setAllToZero():
        for box in TECBoxController._instances:
            box.nursery.start_soon(box.deviceInterface.sendAllToZeroCommand)
            # box.controllerWidget.fillFieldsWithZeros()
            pass

    @staticmethod
    def startSendAll():
        for box in TECBoxController._instances:
            if box.isConnected():
                box.nursery.start_soon(box.sendAll)
            
    async def sendAll(self):
        boxId = self.deviceInterface.boxId
        list = TecControllerInterface.getTecList(boxId)
        count = 0
        for tec in list:
            if self.controllerWidget.check_if_tec_is_enabled(tec.tecNo):
                val = self.controllerWidget.getFieldValue(tec.tecNo)
                if val is not None:
                    await self.deviceInterface.sendTecCommand(tec.tecNo, val)
                    # await self.deviceInterface.addCommandsToOutgoing()  
                    count = count + 1
                    await trio.sleep(0.01 )
        # await self.deviceInterface.startSending()
        await self.terminalManager.addMessage("Sent: "+str(count)+" TEC commands.")
        