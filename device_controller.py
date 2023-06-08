import trio

from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
# from kivy.properties import StringProperty
# from kivy.properties import NumericProperty
# from kivy.properties import BooleanProperty
from kivy.lang import Builder

from terminal_widget import *
from numeric_widgets import FloatInput
from ttf_iface import DIRECTION, TipTiltFocusControlInterface
import re
from enum import IntEnum
from collections import deque
import json

class ControllerState(IntEnum):
    INIT=0
    DISCONNECTED=1
    CONNECT_IN_PROGRESS = 2
    CONNECTED=3
    DISCONNECT_IN_PROGRESS = 4
    
class DeviceController():
    nursery = None
    ControllerState = ControllerState.INIT
    ControllerStateLock = trio.Lock() 
    controllerIpAddr = None
    controllerPort = None
    controllerWidget = None
    terminalManager = None
    debugMode = None
    toggleConnectionRequested = False
    connectedStateHandlerId = None
    connectButtonId = None

    _deviceLabel = "Unlabeled Device"
    
    # deviceInterface = None
    
    def __init__(self, ctrlWidget, nursery, debugMode = False, **kwargs): 
        self.nursery = nursery
        self.controllerWidget = ctrlWidget
        self.debugMode = debugMode
        nursery.start_soon(self.updateControls)
        
    def setDeviceLabel(self, label):
        self._deviceLabel = label
        
    def connectTerminal(self, terminalManager):
        self.terminalManager = terminalManager
    
    def setConnectionInfo(self, ip, port):
        self.controllerIpAddr = ip
        self.controllerPort = port
    
    def setDebugMode(self, mode):
        self.debugMode = mode
    
    def requestConnectionToggle(self):
        self.toggleConnectionRequested = True
            
        
    def registerConnectButtonId(self, _connectButtonId):
        self.connectButtonId = _connectButtonId
        
    async def updateControls(self):
        """Main state machine for handling the controller's events
        """
        self.connectionFailedEvent = trio.Event()
        
        while 1:
            currentState = await self.getControllerState()
            if currentState == ControllerState.INIT:
                await self.initStateHandler()
            elif currentState == ControllerState.DISCONNECTED:
                await self.disconnectedStateHandler()
            elif currentState == ControllerState.CONNECT_IN_PROGRESS:
                if self.debugMode:
                    await trio.sleep(0)
                    self.deviceInterface._connected = True #overriding the pmc connection flag (bad)
                    await self.terminalManager.addMessage(self._deviceLabel + ': Connecting... (debug mode so not really)')
                    await self.__connectionSucceededHandler()
                    # await trio.sleep(0)
                else:
                    await self.connectInProgressStateHandler()
                    if self.connectionFailedEvent.is_set():
                        await self.resetConnection()
                    else:
                        await self.__connectionSucceededHandler()
            elif currentState == ControllerState.CONNECTED:
                await self.__connectedStateHandler()
            elif currentState == ControllerState.DISCONNECT_IN_PROGRESS:
                await self._disconnectInProgressHandler()
            
            if hasattr(self, "updateOutputFields"):
                self.updateOutputFields()
            await trio.sleep(0)
            
    async def setControllerState(self, state):
        await self.ControllerStateLock.acquire()
        self.ControllerState = state
        self.ControllerStateLock.release()
        
    async def getControllerState(self):
        await self.ControllerStateLock.acquire()
        state = self.ControllerState
        self.ControllerStateLock.release()
        return state
         
    async def initStateHandler(self):
            """Performs steps needed to start the state machine correctly
            """
            #Forward the SM to the disconnected state
            await self.setControllerState(ControllerState.DISCONNECTED)
        
    async def disconnectedStateHandler(self):
        """Checks for and deals with events when the SM is in the disconnected state.
        """
        conBtn = self.controllerWidget.ids[self.connectButtonId]
        # disconBtn = self.controllerWidget.ids['disconnect_btn']
        # if len(self.ControllerRequestList) > 0:
        #     request = self.ControllerRequestList.pop()
        #     if request == self.toggleConnectionRequested:
        if self.toggleConnectionRequested:
            self.connectionFailedEvent = trio.Event() #reset the failed connection flag
            await self.terminalManager.addMessage(self._deviceLabel + ': Connecting...')
            await self.setControllerState(ControllerState.CONNECT_IN_PROGRESS)
            conBtn.text = 'Connecting ' + self._deviceLabel
            conBtn.background_color = (0.5,0.5,0.5,1)
            self.toggleConnectionRequested = False
            pass
        await trio.sleep(0)
                
    async def connectInProgressStateHandler(self):
        try:
            await self.deviceInterface.open_connection(self.controllerIpAddr, self.controllerPort)
        except trio.TooSlowError as e:
            await self.terminalManager.addMessage(self._deviceLabel + ': Timed out trying to open TCP Stream', MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        except OSError as e:
            await self.terminalManager.addMessage(self._deviceLabel + ': ' + str(e), MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        # self.nursery.start_soon(pmc.startCommsStream, self.printErrorCallbacks)
        self.nursery.start_soon(self.deviceInterface.startCommsStream, self.printErrorCallbacks)
        await self.deviceInterface.sendHandshake()
        await trio.sleep(0)
        try:
            await self.deviceInterface.waitForHandshakeReply(10)
        except trio.TooSlowError as e:
            await self.terminalManager.addMessage(self._deviceLabel + ': Did not receive handshake reply.', MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        except TimeoutError as e:
            await self.terminalManager.addMessage(self._deviceLabel + ': ' + str(e), MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
    
    # To 
    async def __connectedStateHandler(self):
        conBtn = self.controllerWidget.ids[self.connectButtonId]
        if self.toggleConnectionRequested:
            await self.terminalManager.addMessage(self._deviceLabel + ': Disconnecting...')
            await self.setControllerState(ControllerState.DISCONNECT_IN_PROGRESS)
            conBtn.text = 'Disconnecting ' + self._deviceLabel
            conBtn.background_color = (0.5,0.5,0.5,1)
            self.toggleConnectionRequested = False
            pass
        else:
            if hasattr(self, "connectedStateHandler"):
                await trio.sleep(0)
                await self.connectedStateHandler()
        await trio.sleep(0)
    
    async def _disconnectInProgressHandler(self):
        #Give the child class a chance to send any commands before disconnecting
        if hasattr(self, "disconnectInProgressHandler"):
            await self.disconnectInProgressHandler()
        await self.resetConnection()
        conBtn = self.controllerWidget.ids[self.connectButtonId]
        conBtn.background_color = (1,0,0,1)
        conBtn.text = 'Connect ' + self._deviceLabel
        
    async def resetConnection(self):
        conBtn = self.controllerWidget.ids[self.connectButtonId]
        conBtn.disabled = False
        conBtn.text = 'Connect ' + self._deviceLabel
        conBtn.background_color = (1,0,0,1)
        await self.deviceInterface.Disconnect()
        self.deviceInterface.reset()
        await self.setControllerState(ControllerState.DISCONNECTED)
        
    async def __connectionSucceededHandler(self):
        conBtn = self.controllerWidget.ids[self.connectButtonId]
        await self.setControllerState(ControllerState.CONNECTED)
        await self.terminalManager.addMessage(self._deviceLabel + ': Connected!', MessageType.GOOD_NEWS)
        conBtn.background_color = (0,1,0,1)
        conBtn.text = 'Disconnect ' + self._deviceLabel
        if hasattr(self, "connectionSucceededHandler"):
            await self.connectionSucceededHandler()
    
    
    def printErrorCallbacks(self, excgroup):
        for exc in excgroup.exceptions:
            if isinstance(exc, json.JSONDecodeError):
                self.terminalManager.queueMessage("Failed message decode. [{0}:{1}]. ".format(exc.msg, exc.doc))
                self.terminalManager.queueMessage("Data stream corrupted, you should probably close/reopen")
                self.currentState = ControllerState.INIT
            elif isinstance(exc, trio.BrokenResourceError) or \
                isinstance(exc, trio.ClosedResourceError):
                    pass #Everything is fine, do nothing
            else:
                breakpoint()

                self.terminalManager.queueMessage(exc.msg)
                 
    def defaultButtonPushed(self):
        self.terminalManager.queueMessage('Button not assigned yet!')
        
    def printErrorCallbacks(self, excgroup):
        for exc in excgroup.exceptions:
            if isinstance(exc, json.JSONDecodeError):
                self.terminalManager.queueMessage("Failed message decode. [{0}:{1}]. ".format(exc.msg, exc.doc))
                self.terminalManager.queueMessage("Data stream corrupted, you should probably close/reopen")
                self.currentState = ControllerState.INIT
            elif isinstance(exc, trio.BrokenResourceError) or \
                isinstance(exc, trio.ClosedResourceError):
                    pass #Everything is fine, do nothing
            else:
                breakpoint()
                self.terminalManager.queueMessage(exc.msg)