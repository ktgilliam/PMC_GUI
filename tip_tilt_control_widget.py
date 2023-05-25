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
from pmc_iface import DIRECTION, PrimaryMirrorControl
import re
from enum import IntEnum
from collections import deque
import json

pmc = PrimaryMirrorControl()

class ControllerRequest(IntEnum):
    NO_REQUESTS = 0
    TOGGLE_CONNECTION=1
    GO_HOME_REQUESTED=2
    BOTTOM_FOUND_REQUESTED=3
    TOGGLE_STEPPER_ENABLE=4
    STOP_REQUESTED=5
    
class ControllerState(IntEnum):
    INIT=0
    DISCONNECTED=1
    CONNECT_IN_PROGRESS = 2
    CONNECTED=3
    
class TipTiltControlWidget(GridLayout):   
    singletonControlWidget = None #ObjectProperty(None)
    # test_label_prop = ObjectProperty()
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        if(TipTiltControlWidget.singletonControlWidget == None):
            TipTiltControlWidget.singletonControlWidget = self
        
    def updateOutputFields(self):
        tipValField = self.ids.tip_val
        tipValField.text = str(round(pmc.getCurrentTip(), 4))
        
        tiltValField = self.ids['tilt_val']
        # tiltValField.text = str(pmc._currentTilt)
        tiltValField.text = str(round(pmc.getCurrentTilt(), 4))
        
        focusValField = self.ids['focus_val']
        # focusValField.text = str(pmc._currentFocus)
        focusValField.text = str(round(pmc.getCurrentFocus(), 4))
        
    def enableRelativeControls(self, doEnable):
        buttonFilt = re.compile('do_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = not doEnable
            
            
    def disableControls(self):
        buttonFilt = re.compile('[d|g]o_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = True
        enableStepBtn = self.ids['enable_steppers_btn']
        enableStepBtn.disabled = True
             
    def resetTipTiltStepSizeButtons(self):
        buttonFilt = re.compile('_10*as_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
        
    def resetFocusStepSizeButtons(self):
        buttonFilt = re.compile('_.*um_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
            
            
            
class TipTiltController():
    nursery = None
    ControllerRequestList = deque([])
    ControllerState = ControllerState.INIT
    ControllerStateLock = trio.Lock() 
    controllerIpAddr = None
    controllerPort = None
    controllerWidget = None
    
    def __init__(self, ctrlWidget, nursery, **kwargs): 
        self.nursery = nursery
        self.controllerWidget = ctrlWidget
        nursery.start_soon(self.updateControls)
        
    def connectTerminal(self, terminal):
        self.terminal = terminal
    
    def setConnectionInfo(self, ip, port):
        self.controllerIpAddr = ip
        self.controllerPort = port
        
    async def updateControls(self):
        """Main state machine for handling events in the app
        """
        self.connectionFailedEvent = trio.Event()
        
        while 1:
            currentState = await self.getControllerState()
            if currentState == ControllerState.INIT:
                await self.initStateHandler()
            elif currentState == ControllerState.DISCONNECTED:
                await self.disconnectedStateHandler()
            elif currentState == ControllerState.CONNECT_IN_PROGRESS:
                if self.debug_mode_prop:
                    await trio.sleep(0)
                    pmc._connected = True #overriding the pmc connection flag (bad)
                    await self.terminalManager.addMessage('Connecting... (debug mode so not really)')
                    await trio.sleep(0)
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
            if request == ControllerRequest.TOGGLE_CONNECTION:
                self.connectionFailedEvent = trio.Event() #reset the failed connection flag
                await self.terminalManager.addMessage('Connecting...')
                await self.setControllerState(ControllerState.CONNECT_IN_PROGRESS)
                conBtn.text = 'Connecting...'
                conBtn.background_color = (0.5,0.5,0.5,1)
                pass
        await trio.sleep(0)
                
    async def connectInProgressStateHandler(self):
        try:
            await pmc.open_connection(self.ip_addr_prop, self.port_prop)
        except trio.TooSlowError as e:
            await self.terminalManager.addMessage('Timed out trying to open TCP Stream', MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        except OSError as e:
            await self.terminalManager.addMessage(str(e), MessageType.ERROR)
            self.connectionFailedEvent.set()
            return
        # self.nursery.start_soon(pmc.startCommsStream, self.printErrorCallbacks)
        self.nursery.start_soon(pmc.startCommsStream, self.printErrorCallbacks)
        await pmc.sendHandshake()
        await trio.sleep(0)
        try:
            await pmc.waitForHandshakeReply(10)
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
        await pmc.Disconnect()
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

        goBtn = self.controllerWidget.ids['go_abs_btn']
        conBtn = self.controllerWidget.ids['connect_btn']
        # disconBtn = self.controllerWidget.ids['disconnect_btn']
        enableStepBtn = self.controllerWidget.ids['enable_steppers_btn']
        homeBtn = self.controllerWidget.ids['do_home_all_btn']
        bottomFoundBtn = self.controllerWidget.ids['bottom_found_btn']
        
        if len(self.ControllerRequestList) > 0:
            request = self.ControllerRequestList.pop()
            if request == ControllerRequest.TOGGLE_CONNECTION:
                await self.setControllerState(ControllerState.DISCONNECTED)
                if pmc.steppersEnabled():
                    await pmc.sendEnableSteppers(False)
                    enableStepBtn.text = "Enable Steppers"
                await self.resetConnection()
                await self.terminalManager.addMessage('Disconnected.')
                self.controllerWidget.disableControls()
                conBtn.background_color = (1,0,0,1)
                conBtn.text = 'Connect'
            elif request == ControllerRequest.GO_HOME_REQUESTED:
                homeBtn.text = "Homing..."
                homeBtn.disabled = True
                bottomFoundBtn.disabled = False
                await self.terminalManager.addMessage('Homing. Press step 2 when all motors have bottomed out')
                await pmc.sendHomeAll(self.home_speed_prop)
                await trio.sleep(0)
                homeBtn.disabled = True
                homeBtn.text = "Home All"
                goBtn.disabled = False
            elif request == ControllerRequest.BOTTOM_FOUND_REQUESTED:
                await self.terminalManager.addMessage('Bottom found. Waiting for mirror to return to center...')
                bottomFoundBtn.disabled = True
                await pmc.sendBottomFound()
                await trio.sleep(0)
                try:
                    await pmc.waitForHomingComplete(self.homing_timeout_prop)
                    await self.terminalManager.addMessage('Homing Complete.', MessageType.GOOD_NEWS)
                except trio.TooSlowError as e:
                     await self.terminalManager.addMessage('Homing timed out.', MessageType.ERROR)
                     await pmc.sendStopCommand()
                else:
                    homeBtn.disabled = False
            elif request == ControllerRequest.TOGGLE_STEPPER_ENABLE:
                if pmc.steppersEnabled():
                    await pmc.sendEnableSteppers(False)
                    # TODO: wait for ack before enabling
                    self.controllerWidget.enableRelativeControls(False)
                    # TODO: Ask if system is homed and wait for reply before enabling.
                    goBtn.disabled = True
                    enableStepBtn.text = "Enable Steppers"
                else:
                    await pmc.sendEnableSteppers(True)
                    self.controllerWidget.enableRelativeControls(True)
                    goBtn.disabled = False
                    enableStepBtn.text = "Disable Steppers"
            elif request == ControllerRequest.STOP_REQUESTED:
                await pmc.sendStopCommand()
                    
        await pmc.sendPrimaryMirrorCommands()
        
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
            
    def plusTipButtonPushed(self):
        self.terminalManager.queueMessage(' Tip [+' + str(pmc._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(pmc.TipRelative, DIRECTION.FORWARD)
    
    def minusTipButtonPushed(self):
        self.terminalManager.queueMessage(' Tip [-' + str(pmc._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(pmc.TipRelative,DIRECTION.REVERSE)
        
    def plusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [+' + str(pmc._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(pmc.TiltRelative,DIRECTION.FORWARD)

    def minusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [-' + str(pmc._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(pmc.TiltRelative,DIRECTION.REVERSE)
        
    def plusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [+' + str(pmc._focusStepSize_um) + ' mm]')
        self.nursery.start_soon(pmc.FocusRelative,DIRECTION.FORWARD)
        
    def minusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [-' + str(pmc._focusStepSize_um) + ' mm]')
        self.nursery.start_soon(pmc.FocusRelative,DIRECTION.REVERSE)
            
    def _angleStepSizeButtonPushed(self, stepSize):
        gui = self.root
        pmc._tipTiltStepSize_as = stepSize
        self.controllerWidget.resetTipTiltStepSizeButtons()
        if stepSize == 1.0:
            btn = self.controllerWidget.ids['_1as_btn']
        elif stepSize == 10.0:
            btn = self.controllerWidget.ids['_10as_btn']
        elif stepSize == 100.0:
            btn = self.controllerWidget.ids['_100as_btn']
        elif stepSize == 1000.0:
            btn = self.controllerWidget.ids['_1000as_btn']
        btn.background_color = (0,1,0,1)
        
    def _focusStepSizeButtonPushed(self, stepSize):
        gui = self.root
        pmc._focusStepSize_um = stepSize
        self.controllerWidget.resetFocusStepSizeButtons()
        if stepSize == 0.2:
            btn = self.controllerWidget.ids['_0p2um_btn']
        elif stepSize == 2.0:
            btn = self.controllerWidget.ids['_2um_btn']
        elif stepSize == 20.0:
            btn = self.controllerWidget.ids['_20um_btn']
        elif stepSize == 200.0:
            btn = self.controllerWidget.ids['_200um_btn']
        elif stepSize == 2000.0:
            btn = self.controllerWidget.ids['_2000um_btn']
        btn.background_color = (0,1,0,1)
            
    def AbsGoButtonPushed(self):
        gui = self.root
        tipAbsTI = self.controllerWidget.ids['tip_abs']
        tiltAbsTI = self.controllerWidget.ids['tilt_abs']
        focusAbsTI = self.controllerWidget.ids['focus_abs']
        if len(focusAbsTI.text) > 0: 
            self.nursery.start_soon(pmc.MoveAbsolute,float(tipAbsTI.text), float(tiltAbsTI.text), float(focusAbsTI.text))

    def stopButtonPushed(self):
        pmc.interruptAnything()
                 
    def defaultButtonPushed(self):
        self.terminalManager.queueMessage('Button not assigned yet!')