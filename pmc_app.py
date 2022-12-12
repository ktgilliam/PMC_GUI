from kivy.app import App #, async_runTouchApp
from kivy.uix.settings import SettingsWithSidebar
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window
# from kivy.clock import Clock
import kivy
kivy.require('2.1.0')

import trio
import time


from enum import IntEnum
# from functools import partial
from json_settings import *
import re
from pmc_iface import DIRECTION, PrimaryMirrorControl
import numeric_widgets
from terminal_widget import *

class AppRequest(IntEnum):
    NO_REQUESTS = 0
    CONNECT_REQUESTED=1
    DISCONNECT_REQUESTED=2
    GO_HOME_REQUESTED=3
    
class AppState(IntEnum):
    INIT=0
    DISCONNECTED=1
    CONNECT_IN_PROGRESS = 2
    CONNECTED=3
    
    
Window.size = (900, 650)
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
        
    def enableRelativeControls(self):
        buttonFilt = re.compile('do_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = False
            
    def enableAbsoluteControls(self):
        buttonFilt = re.compile('go_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = False
            
    def disableControls(self):
        buttonFilt = re.compile('[d|g]o_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = True
             
    def resetTipTiltStepSizeButtons(self):
        buttonFilt = re.compile('_10*urad_btn')
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
            
from kivy.clock import Clock
from kivy.config import Config
from collections import deque

class PMC_APP(App):
    nursery = None
    appRequestList = deque([])
    appState = AppState.INIT
    appStateLock = trio.Lock()
    tasksStarted = False
    terminalManager = None
    
    ip_addr_prop = StringProperty()
    port_prop = NumericProperty()
    fan_speed_prop = StringProperty()
    home_speed_prop = StringProperty()
    rel_speed_prop = StringProperty()
    abs_speed_prop = StringProperty()
    debug_mode_prop = BooleanProperty()

    
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        gui = Builder.load_file('pmc_gui.kv')
        # self.terminalManager.addMessage('Welcome. Press F1 for settings.', MessageType.IMPORTANT)
        return gui

    def build_config(self, config):
        config.setdefaults("General", {"dbg_mode":False})
        config.setdefaults("Connection", {"ip_addr": "localhost", "ip_port": 4400})
        config.setdefaults("Speeds", {"fan": 50, "homing": 100, "rel_move": 100, "abs_move": 100})
        return super().build_config(config)
    
    def build_settings(self, settings):
        settings.add_json_panel("General", self.config, data=json_general_settings)
        settings.add_json_panel("Connection", self.config, data=json_connection_settings)
        settings.add_json_panel("Speeds", self.config, data=json_speed_settings)
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
        elif section == "Speeds":
            if key == "fan":
                self.fan_speed_prop = value
            elif key == "homing":
                self.home_speed_prop = value
            elif key == "rel_move":
                self.rel_speed_prop = value
            elif key == "abs_move":
                self.abs_speed_prop = value
        return super().on_config_change(config, section, key, value)
    
    def load_config(self):
        config = super().load_config()
        self.debug_mode_prop = bool(int(config.get('General','dbg_mode')))
        self.ip_addr_prop = config.get('Connection','ip_addr')
        self.port_prop = int(config.get('Connection','ip_port'))
        self.fan_speed_prop = config.get('Speeds','fan')
        self.home_speed_prop = config.get('Speeds','homing')
        self.rel_speed_prop: config.get('Speeds','rel_move')
        self.abs_speed_prop: config.get('Speeds','abs_move')
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
            nursery = self.nursery
            # time.sleep(0.5)
            await trio.sleep(0.1)
            nursery.start_soon(self.initializeTerminal)
            await trio.sleep(0.1)
            nursery.start_soon(self.updateControls)
            self.appState = AppState.INIT
            return False
        
    async def initializeTerminal(self):
        gui = None
        while (gui == None) or (TerminalWidget.terminal == None):
            gui = self.root
            await trio.sleep(0) 
        #terminal object exists, set up the terminal manager...
        self.terminalManager = TerminalManager(TerminalWidget.terminal, self.nursery)
        # await self.terminalManager.initialize(self.nursery)
        await self.terminalManager.addMessage('Welcome. Press F1 for settings.', MessageType.IMPORTANT)
        # while 1:
        #     self.nursery.start_soon(self.terminalManager.updateTerminalWidget)
        #     await trio.sleep(0) 
            
    async def updateControls(self):
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
        await self.setAppState(AppState.DISCONNECTED)
    
    async def disconnectedStateHandler(self):
        gui =  self.root
        conBtn = gui.ids['connect_btn']
        disconBtn = gui.ids['disconnect_btn']
        if len(self.appRequestList) > 0:
            # await trio.sleep(0)
            request = self.appRequestList.pop()
            if request == AppRequest.CONNECT_REQUESTED:
                self.connectionFailedEvent = trio.Event() #reset the failed connection flag
                await self.terminalManager.addMessage('Connecting...')
                await self.setAppState(AppState.CONNECT_IN_PROGRESS)
                conBtn.disabled = True
            elif request == AppRequest.DISCONNECT_REQUESTED:
                await self.terminalManager.addMessage("Disconnect requested from disconnected state", MessageType.WARNING)
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
        
        self.nursery.start_soon(pmc.startCommsStream, self.printErrorCallbacks)
        await pmc.sendHandshake()
        await pmc.sendPrimaryMirrorCommands()
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
        pmc.Disconnect()
        await self.setAppState(AppState.DISCONNECTED)
        
    async def connectionSucceededHandler(self):
        gui =  self.root
        conBtn = gui.ids['connect_btn']
        disconBtn = gui.ids['disconnect_btn']
        gui.enableRelativeControls()
        conBtn.background_color = (0,1,0,1)
        disconBtn.background_color = (1,0,0,1)
        conBtn.text = 'Connected'
        await self.setAppState(AppState.CONNECTED)
        await self.terminalManager.addMessage('Connected!', MessageType.GOOD_NEWS)
        
    async def connectedStateHandler(self):
        gui =  self.root
        conBtn = gui.ids['connect_btn']
        disconBtn = gui.ids['disconnect_btn']
        if len(self.appRequestList) > 0:
            request =   self.appRequestList.pop()
            if request == AppRequest.CONNECT_REQUESTED:
                await self.terminalManager.addMessage("Connect requested from connected state", MessageType.WARNING)
            elif request == AppRequest.DISCONNECT_REQUESTED:
                await self.setAppState(AppState.DISCONNECTED)
                await self.terminalManager.addMessage('Disconnecting.')
                await self.resetConnection()
                gui.disableControls()
                conBtn.background_color = (1,1,1,1)
                disconBtn.background_color = (1,1,1,1)
                disconBtn.disabled = False
                conBtn.text = 'Connect'
            elif request == AppRequest.GO_HOME_REQUESTED:
                await self.terminalManager.addMessage('Homing...')
                pmc.HomeAll()
                gui.enableAbsoluteControls()
        await pmc.sendPrimaryMirrorCommands()
     
    def printErrorCallbacks(self, excgroup):
        for exc in excgroup.exceptions:
            self.terminalManager.queueMessage(exc)
            
    def plusTipButtonPushed(self):
        self.terminalManager.queueMessage(' Tip [+' + str(pmc._tipTiltStepSize_urad) + ' urad]')
        self.nursery.start_soon(pmc.TipRelative, DIRECTION.FORWARD)
    
    def minusTipButtonPushed(self):
        self.terminalManager.queueMessage(' Tip [-' + str(pmc._tipTiltStepSize_urad) + ' urad]')
        self.nursery.start_soon(pmc.TipRelative,DIRECTION.REVERSE)
        
    def plusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [+' + str(pmc._tipTiltStepSize_urad) + ' urad]')
        self.nursery.start_soon(pmc.TiltRelative,DIRECTION.FORWARD)

    def minusTiltButtonPushed(self):
        self.terminalManager.queueMessage(' Tilt [-' + str(pmc._tipTiltStepSize_urad) + ' urad]')
        self.nursery.start_soon(pmc.TiltRelative,DIRECTION.REVERSE)
        
    def plusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [+' + str(pmc._focusStepSize_um) + ' urad]')
        self.nursery.start_soon(pmc.FocusRelative,DIRECTION.FORWARD)
        
    def minusFocusButtonPushed(self):
        self.terminalManager.queueMessage(' Focus [-' + str(pmc._focusStepSize_um) + ' urad]')
        self.nursery.start_soon(pmc.FocusRelative,DIRECTION.REVERSE)
            
    def _1uradButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_urad = 1
        # self.terminalManager.queueMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_1urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _10uradButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_urad = 10
        # self.terminalManager.queueMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_10urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _100uradButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_urad = 100
        # self.terminalManager.queueMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_100urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _1000uradButtonPushed(self):
        gui = self.root
        pmc._tipTiltStepSize_urad = 1000
        # self.terminalManager.queueMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_1000urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _1umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 1
        # self.terminalManager.queueMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_1um_btn']
        btn.background_color = (0,1,0,1)

    def _10umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 10
        # self.terminalManager.queueMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um') 
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_10um_btn']
        btn.background_color = (0,1,0,1)
        
    def _100umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 100
        # self.terminalManager.queueMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_100um_btn']
        btn.background_color = (0,1,0,1)

    def _1000umButtonPushed(self):
        gui = self.root
        pmc._focusStepSize_um = 1000
        # self.terminalManager.queueMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')   
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_1000um_btn']
        btn.background_color = (0,1,0,1) 
             
    def tipAbsGoButtonPushed(self):
        gui = self.root
        tipAbsTI = gui.ids['tip_abs']
        if len(tipAbsTI.text) > 0:
            # self.terminalManager.queueMessage('Mirror Tip set to : ' + str(pmc._currentTip))
            pmc.TipAbsolute(float(tipAbsTI.text))
        
    def tiltAbsGoButtonPushed(self):
        gui = self.root
        tiltAbsTI = gui.ids['tilt_abs']
        if len(tiltAbsTI.text) > 0:  
            # self.terminalManager.queueMessage('Mirror Tilt set to : ' + str(pmc._currentTilt))
            pmc.TiltAbsolute(float(tiltAbsTI.text)  )
        
    def focusAbsGoButtonPushed(self):
        gui = self.root
        focusAbsTI = gui.ids['focus_abs']
        if len(focusAbsTI.text) > 0: 
            # self.terminalManager.queueMessage('Mirror Focus set to : ' + str(pmc._currentFocus))
            pmc.FocusAbsolute(float(focusAbsTI.text)  )
 

        
    def homingButtonPushed(self):
        gui =  self.root
        # self.terminalManager.addMessage('Homing Button Pushed!')


        
    def stopButtonPushed(self):
        self.terminalManager.addMessage('Stop Button Pushed')
                 
    def defaultButtonPushed(self):
        self.terminalManager.addMessage('Button not assigned yet!')



from task_tracer import Tracer, FilterType

if __name__ == "__main__":
    trio.run(PMC_APP().app_func)
    
    # debugTracer = Tracer()
    # debugTracer.addFilters(FilterType.EXCLUDE, 'run_wrapper', 'updateControls', 'TerminalWidget')
    # # debugTracer.addFilters(FilterType.INCLUDE, 'aSendMessages', 'aReceiveMessages', 'startCommsStream')
    # trio.run(PMC_APP().app_func, instruments=[debugTracer])
