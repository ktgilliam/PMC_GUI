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

from enum import Enum
# from functools import partial

class AppState(Enum):
    INIT=0
    INIT_DONE=1
    DISCONNECTED=2
    CONNECTED=3
    
Window.size = (900, 650)
Window.minimum_width, Window.minimum_height = Window.size


from json_settings import *
import re
import pmc_iface
import numeric_widgets
from terminal_widget import TerminalWidget, MessageType

pmc = pmc_iface.PrimaryMirrorControl()

# Uncomment these lines to see all the messages
# from kivy.logger import Logger
# import logging
# Logger.setLevel(logging.TRACE)

# for integrated settings panel: https://kivy.org/doc/stable/api-kivy.app.html?highlight=resize

class PMC_Config(ObjectProperty):
    def test(self):
        pass
    
class PMC_GUI(GridLayout):
    
    _tipTiltStepSize_urad = 1
    _focusStepSize_um = 1
    _currentTip = 0.0
    _currentTilt = 0.0
    _currentFocus = 0.0
    

    
    def updateOutputFields(self):
        tipValField = self.ids['tip_val']
        tipValField.text = str(round(self._currentTip, 4))
        
        tiltValField = self.ids['tilt_val']
        # tiltValField.text = str(gui._currentTilt)
        tiltValField.text = str(round(self._currentTilt, 4))
        
        focusValField = self.ids['focus_val']
        # focusValField.text = str(gui._currentFocus)
        focusValField.text = str(round(self._currentFocus, 4))
        
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
# from functools import partial
from kivy.config import Config
class PMC_APP(App):
    nursery = None
    appState = AppState.INIT
    # ip_addr = ConfigParserProperty()
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
        TerminalWidget.addMessage('Welcome. Press F1 for settings.', MessageType.IMPORTANT)
        Clock.schedule_interval(self.startTasks, 0.5)
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
    
    def startTasks(self, *args):
            nursery = self.nursery
            nursery.start_soon(self.updateTerminal)
            # time.sleep(0.5)
            nursery.start_soon(self.updateControls)
            self.appState = AppState.INIT_DONE
            return False
        
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
                print('App done')
                nursery.cancel_scope.cancel()

            nursery.start_soon(run_wrapper)
            # time.sleep(1)

            
    def plusTipButtonPushed(self):
        gui = self.root
        TerminalWidget.addMessage(' Tip [+' + str(gui._tipTiltStepSize_urad) + ' urad]')
        pmc.TipRelative(gui._tipTiltStepSize_urad)
        gui._currentTip = gui._currentTip + gui._tipTiltStepSize_urad
        gui.updateOutputFields()
        
    def minusTipButtonPushed(self):
        gui = self.root
        TerminalWidget.addMessage(' Tip [-' + str(gui._tipTiltStepSize_urad) + ' urad]')
        pmc.TipRelative(-1*gui._tipTiltStepSize_urad)
        gui._currentTip = gui._currentTip - gui._tipTiltStepSize_urad
        gui.updateOutputFields()
        
    def plusTiltButtonPushed(self):
        gui = self.root
        TerminalWidget.addMessage(' Tilt [+' + str(gui._tipTiltStepSize_urad) + ' urad]')
        pmc.TiltRelative(gui._tipTiltStepSize_urad)
        gui._currentTilt = gui._currentTilt + gui._tipTiltStepSize_urad
        self.updateOutputFields()

    def minusTiltButtonPushed(self):
        gui = self.root
        TerminalWidget.addMessage(' Tilt [-' + str(gui._tipTiltStepSize_urad) + ' urad]')
        pmc.TiltRelative(-1*gui._tipTiltStepSize_urad)
        gui._currentTilt = gui._currentTilt - gui._tipTiltStepSize_urad
        gui.updateOutputFields()
        
    def plusFocusButtonPushed(self):
        gui = self.root
        TerminalWidget.addMessage(' Focus [+' + str(gui._focusStepSize_um) + ' urad]')
        pmc.FocusRelative(gui._focusStepSize_um)
        gui._currentFocus = gui._currentFocus + gui._focusStepSize_um
        gui.updateOutputFields()
        
    def minusFocusButtonPushed(self):
        gui = self.root
        TerminalWidget.addMessage(' Focus [-' + str(gui._focusStepSize_um) + ' urad]')
        pmc.FocusRelative(-1*gui._focusStepSize_um)
        gui._currentFocus = gui._currentFocus - gui._focusStepSize_um
        gui.updateOutputFields()
    

            
    def _1uradButtonPushed(self):
        gui = self.root
        gui._tipTiltStepSize_urad = 1
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_1urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _10uradButtonPushed(self):
        gui = self.root
        gui._tipTiltStepSize_urad = 10
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_10urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _100uradButtonPushed(self):
        gui = self.root
        gui._tipTiltStepSize_urad = 100
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_100urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _1000uradButtonPushed(self):
        gui = self.root
        gui._tipTiltStepSize_urad = 1000
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        gui.resetTipTiltStepSizeButtons()
        btn = gui.ids['_1000urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _1umButtonPushed(self):
        gui = self.root
        gui._focusStepSize_um = 1
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_1um_btn']
        btn.background_color = (0,1,0,1)

    def _10umButtonPushed(self):
        gui = self.root
        gui._focusStepSize_um = 10
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um') 
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_10um_btn']
        btn.background_color = (0,1,0,1)
        
    def _100umButtonPushed(self):
        gui = self.root
        gui._focusStepSize_um = 100
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_100um_btn']
        btn.background_color = (0,1,0,1)

    def _1000umButtonPushed(self):
        gui = self.root
        gui._focusStepSize_um = 1000
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')   
        gui.resetFocusStepSizeButtons()
        btn = gui.ids['_1000um_btn']
        btn.background_color = (0,1,0,1) 
             
    def tipAbsGoButtonPushed(self):
        gui = self.root
        tipAbsTI = gui.ids['tip_abs']
        if len(tipAbsTI.text) > 0:
            gui._currentTip = float(tipAbsTI.text)
            TerminalWidget.addMessage('Mirror Tip set to : ' + str(gui._currentTip))
            pmc.TipAbsolute(gui._currentTip)
            gui.updateOutputFields()
        
    def tiltAbsGoButtonPushed(self):
        gui = self.root
        tiltAbsTI = gui.ids['tilt_abs']
        if len(tiltAbsTI.text) > 0:
            gui._currentTilt = float(tiltAbsTI.text)        
            TerminalWidget.addMessage('Mirror Tilt set to : ' + str(gui._currentTilt))
            pmc.TiltAbsolute(gui._currentTilt)
            self.updateOutputFields()
        
    def focusAbsGoButtonPushed(self):
        gui = self.root
        focusAbsTI = gui.ids['focus_abs']
        if len(focusAbsTI.text) > 0:
            gui._currentFocus = float(focusAbsTI.text)        
            TerminalWidget.addMessage('Mirror Focus set to : ' + str(gui._currentFocus))
            pmc.FocusAbsolute(gui._currentFocus)
            self.updateOutputFields()
 
    def connectButtonPushed(self, _ip, _port):
        gui =  self.root
        conBtn = gui.ids['connect_btn']
        if not pmc.isConnected():
            if self.debug_mode_prop:
               pmc._connected = True #overriding the pmc connection flag (bad)
               TerminalWidget.addMessage("Connected! (debug mode so not really)")
            else:
                TerminalWidget.addMessage('Connecting...')
                self.nursery.start_soon(pmc.Connect, _ip, _port,)
                # pmc.Connect(_ip, _port)
        else:
            pmc.Disonnect()
            gui.disableControls()
            conBtn.background_color = (1,0,0,1)
            conBtn.text = 'Connect'

    def homingButtonPushed(self):
        gui =  self.root
        TerminalWidget.addMessage('Homing Button Pushed!')
        gui._currentTip = 0.0
        gui._currentTilt = 0.0
        gui._currentFocus = 0.0
        pmc.HomeAll(self.home_speed_prop)
        self.enableAbsoluteControls()
        self.updateOutputFields()

        
    def stopButtonPushed(self):
        TerminalWidget.addMessage('Stop Button Pushed')
                 
    def defaultButtonPushed(self):
        TerminalWidget.addMessage('Button not assigned yet!')
        
        
    async def updateControls(self):
        gui = None
        while gui == None:
            await trio.sleep(0.5)
            gui =  self.root
            
        conBtn = gui.ids['connect_btn']
        while 1:
            if self.appState == AppState.INIT_DONE:
                if pmc.isConnected():
                    gui.enableRelativeControls()
                    if pmc.isHomed():
                        self.enableAbsoluteControls()
                    conBtn.background_color = (0,1,0,1)
                    conBtn.text = 'Connected'
                else:
                    gui.disableControls()
            await trio.sleep(0)
            
    async def updateTerminal(self):
        gui = None
        while (gui == None) or (TerminalWidget.terminal == None):
            gui = self.root
            # await trio.sleep(0.1)
            time.sleep(0.1)
        while 1:
            TerminalWidget.terminal.printMessages()
            await trio.sleep(0)
            #     trio.sleep(0.1)
            
if __name__ == "__main__":
    # PMC_APP().run()
    trio.run(PMC_APP().app_func)
    