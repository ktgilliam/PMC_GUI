import trio
import kivy
kivy.require('2.1.0')
from kivy.app import App #, async_runTouchApp
from kivy.uix import tabbedpanel
from kivy.uix.settings import SettingsWithSidebar
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window
# from kivy.clock import Clock
# from kivy.config import Config


from json_settings import *


# from pmc_iface import DIRECTION, PrimaryMirrorControl
from terminal_widget import *
from tip_tilt_control_widget import *
from tec_control_widget import *

from numeric_widgets import FloatInput

Window.size = (1100, 700)
Window.minimum_width, Window.minimum_height = Window.size

# Uncomment these lines to see all the messages
# from kivy.logger import Logger
# import logging
# Logger.setLevel(logging.TRACE)

# for integrated settings panel: https://kivy.org/doc/stable/api-kivy.app.html?highlight=resize



class PMC_GUI(GridLayout):
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
    
       
class PMC_APP(App):
    nursery = None
    tasksStarted = False
    terminalManager = None
    tipTiltController = None
    tecBox_A = None
    tecBox_B = None
    
    ip_addr_prop = StringProperty()
    tip_tilt_port_prop = NumericProperty()
    tec_a_port_prop = NumericProperty()
    tec_b_port_prop = NumericProperty()
    fan_speed_prop = NumericProperty()
    home_speed_prop = NumericProperty()
    homing_timeout_prop = NumericProperty()
    rel_speed_prop = NumericProperty()
    abs_speed_prop = NumericProperty()
    debug_mode_prop = BooleanProperty()

    
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        Builder.load_file('kv_files/util_widgets.kv')
        Builder.load_file('kv_files/tip_tilt_control_widget.kv')
        Builder.load_file('kv_files/tec_control_widget.kv')
        Builder.load_file('kv_files/terminal_widget.kv')
        gui = Builder.load_file('kv_files/pmc_gui.kv')
        return gui

    def build_config(self, config):
        config.setdefaults("Connection", {"ip_addr": "localhost", "tip_tilt_ip_port": 4400, "tec_a_ip_port": 4500, "tec_b_ip_port": 4500})
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
                self.tipTiltController.setDebugMode(self.debug_mode_prop)
        elif section == "Connection":
            if key == "ip_addr":
                self.ip_addr_prop = value
            elif key == "tip_tilt_ip_port":
                self.tip_tilt_port_prop = int(value)
            elif key == "tecBoxA_ip_port":
                self.tecBoxA_port_prop = int(value)
            elif key == "tecBoxB_ip_port":
                self.tecBoxB_port_prop = int(value)
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
        self.ip_addr_prop = config.get('Connection','ip_addr')
        self.tip_tilt_port_prop = int(config.get('Connection','tip_tilt_ip_port'))
        self.tec_a_port_prop = int(config.get('Connection','tec_a_ip_port'))
        self.tec_b_port_prop = int(config.get('Connection','tec_b_ip_port'))
        self.fan_speed_prop = int(config.get('Motion','fan_speed'))
        self.home_speed_prop = int(config.get('Motion','homing_speed'))
        self.homing_timeout_prop = int(config.get('Motion','homing_timeout'))
        self.rel_speed_prop: int(config.get('Motion','rel_move'))
        self.abs_speed_prop: int(config.get('Motion','abs_move'))
        self.debug_mode_prop: config.get('General', 'dbg_mode')=='True'
        return config
            
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
        nursery.start_soon(self.initializeTipTiltControl)
        nursery.start_soon(self.initializeTECControl)

        
    async def initializeTerminal(self):
        """Creates the terminal object and stores it as a variable
        """
        gui = None
        while (gui is None) or (TerminalWidget.terminal is None):
            gui = self.root
            await trio.sleep(0) 
        #terminal object exists, set up the terminal manager...
        self.terminalManager = TerminalManager(TerminalWidget.terminal, self.nursery)
        await self.terminalManager.addMessage('Welcome. Press F1 for settings.', MessageType.IMPORTANT)

    async def initializeTipTiltControl(self):
        while (TipTiltControlWidget.singletonControlWidget is None):
            await trio.sleep(0) 
        self.tipTiltController = TipTiltController(self.root.ids.tipTiltCtrl, self.nursery, self.debug_mode_prop)
        self.tipTiltController.setConnectionInfo(self.ip_addr_prop, self.tip_tilt_port_prop)
        self.tipTiltController.registerConnectButtonId('tip_tilt_connect_btn')
        self.tipTiltController.setDeviceLabel('Tip/Tilt/Focus')
        self.tipTiltController.connectTerminal(self.terminalManager)
        
    async def initializeTECControl(self):
        # while (TECControlWidget.singletonControlWidget is None):
        #     await trio.sleep(0) 
        self.tecBox_A = TECBoxController(self.root.ids.tecCtrl, self.nursery, self.debug_mode_prop)
        self.tecBox_A.setConnectionInfo(self.ip_addr_prop, self.tec_a_port_prop)
        self.tecBox_A.registerConnectButtonId('tec_connect_a_btn')
        self.tecBox_A.setDeviceLabel('TEC Box A')
        self.tecBox_A.connectTerminal(self.terminalManager)
        
        self.tecBox_B = TECBoxController(self.root.ids.tecCtrl, self.nursery, self.debug_mode_prop)
        self.tecBox_B.setConnectionInfo(self.ip_addr_prop, self.tec_a_port_prop)
        self.tecBox_B.registerConnectButtonId('tec_connect_b_btn')
        self.tecBox_B.setDeviceLabel('TEC Box B')
        self.tecBox_B.connectTerminal(self.terminalManager)
         
         
from task_tracer import Tracer, FilterType

if __name__ == "__main__":
    trio.run(PMC_APP().app_func)
    
    # debugTracer = Tracer()
    # debugTracer.addFilters(FilterType.EXCLUDE, 'run_wrapper', 'updateControls', 'TerminalWidget')
    # # debugTracer.addFilters(FilterType.INCLUDE, 'aSendMessages', 'aReceiveMessages', 'startCommsStream')
    # trio.run(PMC_APP().app_func, instruments=[debugTracer])
