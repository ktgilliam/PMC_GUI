import trio
import kivy
kivy.require('2.1.0')
from kivy.app import App #, async_runTouchApp
from kivy.uix.settings import SettingsWithSidebar
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window
# from kivy.clock import Clock
# from kivy.config import Config
from collections import deque
from enum import IntEnum
from json_settings import *
import re
from pmc_iface import DIRECTION, PrimaryMirrorControl
from terminal_widget import *
from numeric_widgets import FloatInput

class AppRequest(IntEnum):
    NO_REQUESTS = 0
    CONNECT_REQUESTED=1
    DISCONNECT_REQUESTED=2
    GO_HOME_REQUESTED=3
    TOGGLE_STEPPER_ENABLE=4
    STOP_REQUESTED=5
class AppState(IntEnum):
    INIT=0
    DISCONNECTED=1
    CONNECT_IN_PROGRESS = 2
    CONNECTED=3
    
    
Window.size = (900, 700)
Window.minimum_width, Window.minimum_height = Window.size

pmc = PrimaryMirrorControl()

# Uncomment these lines to see all the messages
# from kivy.logger import Logger
# import logging
# Logger.setLevel(logging.TRACE)

# for integrated settings panel: https://kivy.org/doc/stable/api-kivy.app.html?highlight=resize



class PMC_GUI(GridLayout):
    
    def updateOutputFields(self):
        tipValField = self.ids['tip_val']
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
        buttonFilt = re.compile('_10*mas_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
        
    def resetFocusStepSizeButtons(self):
        buttonFilt = re.compile('_10*um_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
            


class PMC_APP(App):
    nursery = None
    appRequestList = deque([])
    appState = AppState.INIT
    appStateLock = trio.Lock()
    tasksStarted = False
    terminalManager = None
    
    ip_addr_prop = StringProperty()
    port_prop = NumericProperty()
    fan_speed_prop = NumericProperty()
    home_speed_prop = NumericProperty()
    homing_timeout_prop = NumericProperty()
    rel_speed_prop = NumericProperty()
    abs_speed_prop = NumericProperty()
    debug_mode_prop = BooleanProperty()

    
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        gui = Builder.load_file('pmc_gui.kv')
        return gui

    def build_config(self, config):
        config.setdefaults("Connection", {"ip_addr": "localhost", "ip_port": 4400})
        config.setdefaults("Motion", {"fan_speed":50, "homing_speed":100, "homing_timeout":60, "rel_move": 100, "abs_move": 100})
        config.setdefaults("General", {"dbg_mode":False})
        return super().build_config(config)
    
    def build_settings(self, settings):
        settings.add_json_panel("Connection", self.config, data=json_connection_settings)
        settings.add_json_panel("Motion", self.config, data=json_motion_settings)
        settings.add_json_panel("General", self.config, data=json_general_settings)
        return super().build_settings(settings)

    def on_config_change(self, config, section, key, value):
        if section == "General":
            if key == "dbg_mode":
                self.debug_mode_prop = bool(int(value))
        elif section == "Connection":
            if key == "ip_addr":
                self.ip_addr_prop = value
            elif key == "ip_port":
                self.port_prop = int(value)
        elif section == "Motion":
            if key == "fan":
                self.fan_speed_prop = int(value)
            elif key == "homing_speed":
                self.home_speed_prop = int(value)
            elif key == "homing_timeout":
                self.homing_timeout_prop = int(value)
            elif key == "rel_move":
                self.rel_speed_prop = int(value)
            elif key == "abs_move":
                self.abs_speed_prop = int(value)
        return super().on_config_change(config, section, key, value)
    
    def load_config(self):
        config = super().load_config()
        self.debug_mode_prop = bool(config.get('General','dbg_mode')=='True')
        self.ip_addr_prop = config.get('Connection','ip_addr')
        self.port_prop = int(config.get('Connection','ip_port'))
        self.fan_speed_prop = int(config.get('Motion','fan_speed'))
        self.home_speed_prop = int(config.get('Motion','homing_speed'))
        self.homing_timeout_prop = int(config.get('Motion','homing_timeout'))
        self.rel_speed_prop: int(config.get('Motion','rel_move'))
        self.abs_speed_prop: int(config.get('Motion','abs_move'))
        self.debug_mode_prop: config.get('General', 'dbg_mode')=='True'
        return config
    
    async def setAppState(self, state):
        await self.appStateLock.acquire()
        self.appState = state
        self.appStateLock.release()
        
    async def getAppState(self):
        await self.appStateLock.acquire()
        state = self.appState
        self.appStateLock.release()
        return state
        
    async def app_func(self):
        '''trio needs to run a function, so this is it. '''
        async with trio.open_nursery() as nursery:
            '''In trio you create a nursery, in which you schedule async
            functions to be run by the nursery simultaneously as tasks.
            This will run all two methods starting in random order
            asynchronously and then block until they are finished or canceled
            at the `with` level. '''
            self.nursery = nursery

            async def run_wrapper():
                # trio needs to be set so that it'll be used for the event loop
                await self.async_run(async_lib='trio')
                # time.sleep(0.5) #asynchronous delay to give the gui time to get moving
                
                print('App done')
                nursery.cancel_scope.cancel()

            nursery.start_soon(run_wrapper)
            nursery.start_soon(self.launchTasks)
            
    async def launchTasks(self):
        """Starts the tasks for the terminal and the main state machine
        """
        nursery = self.nursery
        # time.sleep(0.5)
        await trio.sleep(0.1)
        nursery.start_soon(self.initializeTerminal)
        await trio.sleep(0.1)
        nursery.start_soon(self.updateControls)
        self.appState = AppState.INIT

        
    async def initializeTerminal(self):
        """Creates the terminal object and stores it as a variable
        """
        gui = None
        while (gui == None) or (TerminalWidget.terminal == None):
            gui = self.root
            await trio.sleep(0) 
        #terminal object exists, set up the terminal manager...
        self.terminalManager = TerminalManager(TerminalWidget.terminal, self.nursery)
        await self.terminalManager.addMessage('Welcome. Press F1 for settings.', MessageType.IMPORTANT)

    async def updateControls(self):
        """Main state machine for handling events in the app
        """
        gui = None
        while gui == None:
            gui =  self.root
            await trio.sleep(0)

        self.connectionFailedEvent = trio.Event()
        
        while 1:
            currentState = await self.getAppState()
            if currentState == AppState.INIT:
                await self.initStateHandler()
            elif currentState == AppState.DISCONNECTED:
                await self.disconnectedStateHandler()
            elif currentState == AppState.CONNECT_IN_PROGRESS:
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
            elif currentState == AppState.CONNECTED:
                await self.connectedStateHandler()                
            gui.updateOutputFields()
            await trio.sleep(0)


    async def initStateHandler(self):
        """Performs steps needed to start the state machine correctly
        """
        #Forward the SM to the disconnected state
        await self.setAppState(AppState.DISCONNECTED)
    
    async def disconnectedStateHandler(self):
        """Checks for and deals with events when the SM is in the disconnected state.
        """
        gui =  self.root
        conBtn = gui.ids['connect_btn']
        disconBtn = gui.ids['disconnect_btn']
        if len(self.appRequestList) > 0:
            request = self.appRequestList.pop()
            if request == AppRequest.CONNECT_REQUESTED:
                self.connectionFailedEvent = trio.Event() #reset the failed connection flag
                await self.terminalManager.addMessage('Connecting...')
                await self.setAppState(AppState.CONNECT_IN_PROGRESS)
                conBtn.disabled = True
            elif request == AppRequest.DISCONNECT_REQUESTED:
                # await self.terminalManager.addMessage("Disconnect requested from disconnected state", MessageType.WARNING)
                pass
        await trio.sleep(0)
                
    async def connectInProgressStateHandler(self):
        gui =  self.root
        conBtn = gui.ids['connect_btn']
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
        gui =  self.root
        conBtn = gui.ids['connect_btn']
        conBtn.disabled = False
        await pmc.Disconnect()
        await self.setAppState(AppState.DISCONNECTED)
        
    async def connectionSucceededHandler(self):
        gui =  self.root
        conBtn = gui.ids['connect_btn']
        conBtn.background_color = (0,1,0,1)
        conBtn.text = 'Connected'
        disconBtn = gui.ids['disconnect_btn']
        disconBtn.background_color = (1,0,0,1)
        disconBtn.disabled = False
        enableStepBtn = gui.ids['enable_steppers_btn']
        enableStepBtn.disabled = False
        
        await self.setAppState(AppState.CONNECTED)
        await self.terminalManager.addMessage('Connected!', MessageType.GOOD_NEWS)
        
    async def connectedStateHandler(self):
        gui =  self.root
        goBtn = gui.ids['go_abs_btn']
        conBtn = gui.ids['connect_btn']
        disconBtn = gui.ids['disconnect_btn']
        enableStepBtn = gui.ids['enable_steppers_btn']
        if len(self.appRequestList) > 0:
            request = self.appRequestList.pop()
            if request == AppRequest.CONNECT_REQUESTED:
                # await self.terminalManager.addMessage("Connect requested from connected state", MessageType.WARNING)
                pass
            elif request == AppRequest.DISCONNECT_REQUESTED:
                await self.setAppState(AppState.DISCONNECTED)
                await self.resetConnection()
                await self.terminalManager.addMessage('Disconnected.')
                gui.disableControls()
                conBtn.background_color = (1,1,1,1)
                disconBtn.background_color = (1,1,1,1)
                disconBtn.disabled = True
                conBtn.text = 'Connect'
            elif request == AppRequest.GO_HOME_REQUESTED:
                homeBtn = gui.ids['do_home_all_btn']
                homeBtn.text = "Homing..."
                homeBtn.disabled = True
                await self.terminalManager.addMessage('Homing...')
                await pmc.sendHomeAll(self.home_speed_prop)
                await trio.sleep(0)
                try:
                    await pmc.waitForHomingComplete(self.homing_timeout_prop)
                    await self.terminalManager.addMessage('Homing Complete.', MessageType.GOOD_NEWS)
                except trio.TooSlowError as e:
                     await self.terminalManager.addMessage('Homing timed out.', MessageType.ERROR)
                     await pmc.sendStopCommand()
                     
                homeBtn.disabled = False
                homeBtn.text = "Home All"
                goBtn.disabled = False
            elif request == AppRequest.TOGGLE_STEPPER_ENABLE:
                if pmc.steppersEnabled():
                    await pmc.sendEnableSteppers(False)
                    # TODO: wait for ack before enabling
                    gui.enableRelativeControls(False)
                    # TODO: Ask if system is homed and wait for reply before enabling.
                    goBtn.disabled = True
                    enableStepBtn.text = "Enable Steppers"
                else:
                    await pmc.sendEnableSteppers(True)
                    gui.enableRelativeControls(True)
                    goBtn.disabled = False
                    enableStepBtn.text = "Disable Steppers"
            elif request == AppRequest.STOP_REQUESTED:
                await pmc.sendStopCommand()
                    
        await pmc.sendPrimaryMirrorCommands()
        
    def printErrorCallbacks(self, excgroup):
        for exc in excgroup.exceptions:
            if isinstance(exc, json.JSONDecodeError):
                self.terminalManager.queueMessage("Failed message decode. [{0}:{1}]. ".format(exc.msg, exc.doc))
                self.terminalManager.queueMessage("Data stream corrupted, you should probably close/reopen")
                self.currentState = AppState.INIT
            elif isinstance(exc, trio.BrokenResourceError) or \
                isinstance(exc, trio.ClosedResourceError):
                    pass #Everything is fine, do nothing
            else:
                breakpoint()

                self.terminalManager.queueMessage(exc.msg)
            
    def plusTipButtonPushed(self):
        self.terminalManager.queueMessage(' Tip [+' + str(pmc._tipTiltStepSize_mas) + ' mas]')
        self.nursery.start_soon(pmc.TipRelative, DIRECTION.FORWARD)
    
    def minusTipButtonPushed(self):
        self.terminalManager.queueMessage(' Tip [-' + str(pmc._tipTiltStepSize_mas) + ' mas]')
        self.nursery.start_soon(pmc.TipRelative,DIRECTION.REVERSE)
        
    def plusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [+' + str(pmc._tipTiltStepSize_mas) + ' mas]')
        self.nursery.start_soon(pmc.TiltRelative,DIRECTION.FORWARD)

    def minusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [-' + str(pmc._tipTiltStepSize_mas) + ' mas]')
        self.nursery.start_soon(pmc.TiltRelative,DIRECTION.REVERSE)
        
    def plusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [+' + str(pmc._focusStepSize_um) + ' um]')
        self.nursery.start_soon(pmc.FocusRelative,DIRECTION.FORWARD)
        
    def minusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [-' + str(pmc._focusStepSize_um) + ' um]')
        self.nursery.start_soon(pmc.FocusRelative,DIRECTION.REVERSE)
            
    def _1masButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_mas = 1
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_1mas_btn']
        btn.background_color = (0,1,0,1)
        
    def _10masButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_mas = 10
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_10mas_btn']
        btn.background_color = (0,1,0,1)
        
    def _100masButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_mas = 100
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_100mas_btn']
        btn.background_color = (0,1,0,1)
        
    def _1000masButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_mas = 1000
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_1000mas_btn']
        btn.background_color = (0,1,0,1)
        
    def _1umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 1
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_1um_btn']
        btn.background_color = (0,1,0,1)

    def _10umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 10
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_10um_btn']
        btn.background_color = (0,1,0,1)
        
    def _100umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 100
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_100um_btn']
        btn.background_color = (0,1,0,1)

    def _1000umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 1000
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_1000um_btn']
        btn.background_color = (0,1,0,1) 
            
    def AbsGoButtonPushed(self):
        gui = self.root
        tipAbsTI = gui.ids['tip_abs']
        tiltAbsTI = gui.ids['tilt_abs']
        focusAbsTI = gui.ids['focus_abs']
        if len(focusAbsTI.text) > 0: 
            self.nursery.start_soon(pmc.MoveAbsolute,float(tipAbsTI.text), float(tiltAbsTI.text), float(focusAbsTI.text))

    def stopButtonPushed(self):
        pmc.interruptAnything()
                 
    def defaultButtonPushed(self):
        self.terminalManager.queueMessage('Button not assigned yet!')



from task_tracer import Tracer, FilterType

if __name__ == "__main__":
    trio.run(PMC_APP().app_func)
    
    # debugTracer = Tracer()
    # debugTracer.addFilters(FilterType.EXCLUDE, 'run_wrapper', 'updateControls', 'TerminalWidget')
    # # debugTracer.addFilters(FilterType.INCLUDE, 'aSendMessages', 'aReceiveMessages', 'startCommsStream')
    # trio.run(PMC_APP().app_func, instruments=[debugTracer])
