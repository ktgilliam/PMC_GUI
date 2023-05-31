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

from device_controller import DeviceController

ttfIface = TipTiltFocusControlInterface()

class ControllerRequest(IntEnum):
    NO_REQUESTS = 0
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
        tipValField.text = str(round(ttfIface.getCurrentTip(), 4))
        
        tiltValField = self.ids['tilt_val']
        # tiltValField.text = str(pmc._currentTilt)
        tiltValField.text = str(round(ttfIface.getCurrentTilt(), 4))
        
        focusValField = self.ids['focus_val']
        # focusValField.text = str(pmc._currentFocus)
        focusValField.text = str(round(ttfIface.getCurrentFocus(), 4))
        
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
            
            
            
class TipTiltController(DeviceController):
    ControllerRequestList = deque([])
    
    def __init__(self, ctrlWidget, nursery, debugMode, **kwargs): 
        super().__init__(ctrlWidget, nursery, debugMode)
        ttfIface.setDebugMode(debugMode)
        # self.registerConnectedStateHandler(self.tipTiltConnectedStateHandler)
        self.registerConnectButtonId('connect_btn')
        
    async def connectedStateHandler(self):
        goBtn = self.controllerWidget.ids['go_abs_btn']
        # disconBtn = self.controllerWidget.ids['disconnect_btn']
        enableStepBtn = self.controllerWidget.ids['enable_steppers_btn']
        homeBtn = self.controllerWidget.ids['do_home_all_btn']
        bottomFoundBtn = self.controllerWidget.ids['bottom_found_btn']
        
        if len(self.ControllerRequestList) > 0:
            request = self.ControllerRequestList.pop()
            if request == ControllerRequest.GO_HOME_REQUESTED:
                homeBtn.text = "Homing..."
                homeBtn.disabled = True
                bottomFoundBtn.disabled = False
                await self.terminalManager.addMessage('Homing. Press step 2 when all motors have bottomed out')
                await ttfIface.sendHomeAll(self.home_speed_prop)
                await trio.sleep(0)
                homeBtn.disabled = True
                homeBtn.text = "Home All"
                goBtn.disabled = False
            elif request == ControllerRequest.BOTTOM_FOUND_REQUESTED:
                await self.terminalManager.addMessage('Bottom found. Waiting for mirror to return to center...')
                bottomFoundBtn.disabled = True
                await ttfIface.sendBottomFound()
                await trio.sleep(0)
                try:
                    await ttfIface.waitForHomingComplete(self.homing_timeout_prop)
                    await self.terminalManager.addMessage('Homing Complete.', MessageType.GOOD_NEWS)
                except trio.TooSlowError as e:
                    await self.terminalManager.addMessage('Homing timed out.', MessageType.ERROR)
                    await ttfIface.sendStopCommand()
                else:
                    homeBtn.disabled = False
            elif request == ControllerRequest.TOGGLE_STEPPER_ENABLE:
                if ttfIface.steppersEnabled():
                    await ttfIface.sendEnableSteppers(False)
                    # TODO: wait for ack before enabling
                    self.controllerWidget.enableRelativeControls(False)
                    # TODO: Ask if system is homed and wait for reply before enabling.
                    goBtn.disabled = True
                    enableStepBtn.text = "Enable Steppers"
                else:
                    await ttfIface.sendEnableSteppers(True)
                    self.controllerWidget.enableRelativeControls(True)
                    goBtn.disabled = False
                    enableStepBtn.text = "Disable Steppers"
            elif request == ControllerRequest.STOP_REQUESTED:
                await ttfIface.sendStopCommand() 
        await ttfIface.sendCommands()
            
    async def disconnectInProgressHandler(self):
        enableStepBtn = self.controllerWidget.ids['enable_steppers_btn']
        if ttfIface.steppersEnabled():
            await ttfIface.sendEnableSteppers(False)
            enableStepBtn.text = "Enable Steppers"
        self.controllerWidget.disableControls()
        
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
        self.terminalManager.queueMessage(' Tip [+' + str(ttfIface._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(ttfIface.TipRelative, DIRECTION.FORWARD)
    
    def minusTipButtonPushed(self):
        self.terminalManager.queueMessage(' Tip [-' + str(ttfIface._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(ttfIface.TipRelative,DIRECTION.REVERSE)
        
    def plusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [+' + str(ttfIface._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(ttfIface.TiltRelative,DIRECTION.FORWARD)

    def minusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [-' + str(ttfIface._tipTiltStepSize_as) + ' as]')
        self.nursery.start_soon(ttfIface.TiltRelative,DIRECTION.REVERSE)
        
    def plusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [+' + str(ttfIface._focusStepSize_um) + ' mm]')
        self.nursery.start_soon(ttfIface.FocusRelative,DIRECTION.FORWARD)
        
    def minusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [-' + str(ttfIface._focusStepSize_um) + ' mm]')
        self.nursery.start_soon(ttfIface.FocusRelative,DIRECTION.REVERSE)
            
    def _angleStepSizeButtonPushed(self, stepSize):
        gui = self.root
        ttfIface._tipTiltStepSize_as = stepSize
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
        ttfIface._focusStepSize_um = stepSize
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
            self.nursery.start_soon(ttfIface.MoveAbsolute,float(tipAbsTI.text), float(tiltAbsTI.text), float(focusAbsTI.text))

    def stopButtonPushed(self):
        ttfIface.interruptAnything()
                 
    def defaultButtonPushed(self):
        self.terminalManager.queueMessage('Button not assigned yet!')