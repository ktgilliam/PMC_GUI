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

ttfIface = TipTiltFocusControlInterface()
    
class ControllerState(IntEnum):
    INIT=0
    DISCONNECTED=1
    CONNECT_IN_PROGRESS = 2
    CONNECTED=3           
            
            
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
    connectedStateHandler = None
    
    def __init__(self, ctrlWidget, nursery, debugMode = False, **kwargs): 
        self.nursery = nursery
        self.controllerWidget = ctrlWidget
        self.debugMode = debugMode
        nursery.start_soon(self.updateControls)
        
    def connectTerminal(self, terminalManager):
        self.terminalManager = terminalManager
    
    def setConnectionInfo(self, ip, port):
        self.controllerIpAddr = ip
        self.controllerPort = port
    
    def setDebugMode(self, mode):
        self.debugMode = mode
    
    def toggleConnectionRequest(self):
        toggleConnectionRequested = True
            
    def registerConnectedStateHandler(self, sh):
        self.connectedStateHandler = sh
        
    async def updateControls(self):
        """Main state machine for handling tip/tilt events
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
                    ttfIface._connected = True #overriding the pmc connection flag (bad)
                    await self.terminalManager.addMessage('Connecting... (debug mode so not really)')
                    await self.connectionSucceededHandler()
                    # await trio.sleep(0)
                else:
                    await self.connectInProgressStateHandler()
                    if self.connectionFailedEvent.is_set():
                        await self.resetConnection()
                    else:
                        await self.connectionSucceededHandler()
            elif currentState == ControllerState.CONNECTED:
                await self.connectedStateHandler()                
            self.controllerWidget.updateOutputFields()
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
        conBtn = self.controllerWidget.ids['connect_btn']
        # disconBtn = self.controllerWidget.ids['disconnect_btn']
        if len(self.ControllerRequestList) > 0:
            request = self.ControllerRequestList.pop()
            if request == self.toggleConnectionRequested:
                self.connectionFailedEvent = trio.Event() #reset the failed connection flag
                await self.terminalManager.addMessage('Connecting...')
                await self.setControllerState(ControllerState.CONNECT_IN_PROGRESS)
                conBtn.text = 'Connecting...'
                conBtn.background_color = (0.5,0.5,0.5,1)
                pass
        await trio.sleep(0)
                
    async def connectInProgressStateHandler(self):
        try:
            await ttfIface.open_connection(self.controllerIpAddr, self.controllerPort)
        except trio.TooSlowError as e:
            await self.terminalManager.addMessage('Timed out trying to open TCP Stream', MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        except OSError as e:
            await self.terminalManager.addMessage(str(e), MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        # self.nursery.start_soon(pmc.startCommsStream, self.printErrorCallbacks)
        self.nursery.start_soon(ttfIface.startCommsStream, self.printErrorCallbacks)
        await ttfIface.sendHandshake()
        await trio.sleep(0)
        try:
            await ttfIface.waitForHandshakeReply(10)
        except trio.TooSlowError as e:
            await self.terminalManager.addMessage('Did not receive handshake reply.', MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        except TimeoutError as e:
            await self.terminalManager.addMessage(str(e), MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
            
    async def resetConnection(self):

        conBtn = self.controllerWidget.ids['connect_btn']
        conBtn.disabled = False
        conBtn.text = 'Connect'
        conBtn.background_color = (1,0,0,1)
        await ttfIface.Disconnect()
        ttfIface.ttf_reset()
        await self.setControllerState(ControllerState.DISCONNECTED)
        
    async def connectionSucceededHandler(self):
        conBtn = self.controllerWidget.ids['connect_btn']
        enableStepBtn = self.controllerWidget.ids['enable_steppers_btn']
        enableStepBtn.disabled = False
        await self.setControllerState(ControllerState.CONNECTED)
        await self.terminalManager.addMessage('Connected!', MessageType.GOOD_NEWS)
        conBtn.background_color = (0,1,0,1)
        conBtn.text = 'Disconnect'
        
    
    async def connectedStateHandler(self):
        if self.connectedStateHandler != None:
            self.connectedStateHandler()

        
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