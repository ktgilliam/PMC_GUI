import json
import numeric_widgets
from os.path import exists
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

from terminal_widget import TerminalWidget


Builder.load_file('pmc_config_gui.kv')

class PMC_Config_GUI(Screen):
    # pass
    ip_addr_prop = StringProperty()
    port_prop = StringProperty()
    fan_speed_prop = StringProperty()
    home_speed_prop = StringProperty()
    rel_speed_prop = StringProperty()
    abs_speed_prop = StringProperty()
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        file_exists = exists("config.json")
        if not file_exists:
            self.writeDefaultConfig()
        self.readConfig()
        
    def resetDefaultConfig(self):
        self.writeDefaultConfig()
        self.readConfig()
        
    def writeDefaultConfig(self):
        f = open("config.json", "w")
        configJson = {}
        configJson['PMC_Config'] = {}
        configJson['PMC_Config']['Connection'] = {}
        configJson['PMC_Config']['Connection']['IP_Address'] = None
        configJson['PMC_Config']['Connection']['Port'] = None
        configJson['PMC_Config']['Speeds'] = {}
        configJson['PMC_Config']['Speeds']['Fan'] = 50
        configJson['PMC_Config']['Speeds']['Homing'] = 100
        configJson['PMC_Config']['Speeds']['RelativeMove'] = 100.0
        configJson['PMC_Config']['Speeds']['AbsoluteMove'] = 100.0
        configJsonObject = json.dumps(configJson, indent=4)
        f.write(configJsonObject)
        f.close()
        TerminalWidget.addMessage('Wrote default config file')
        
    def readConfig(self):
        file_exists = exists("config.json")
        if not file_exists:
            self.writeDefaultConfig()
        f = open("config.json", "r")
        configStr = f.read()
        f.close()
        configJson = json.loads(configStr)
        
        # try:
        ipString = configJson['PMC_Config']['Connection']['IP_Address']
        if ipString == None:
            ipString = ''
        self.ip_addr_prop = ipString
        
        portNoInt = configJson['PMC_Config']['Connection']['Port']
        if portNoInt == None:
            self.port_prop = ''
        else:
            self.port_prop = str(portNoInt)
        
        self.fan_speed_prop = str(configJson['PMC_Config']['Speeds']['Fan'])
        self.home_speed_prop = str(configJson['PMC_Config']['Speeds']['Homing'])
        self.rel_speed_prop = str(configJson['PMC_Config']['Speeds']['RelativeMove'])
        self.abs_speed_prop = str(configJson['PMC_Config']['Speeds']['AbsoluteMove'])

    
    def saveConfig(self):
        f = open("config.json", "w")
        configJson = {}
        configJson['PMC_Config'] = {}
        configJson['PMC_Config']['Connection'] = {}
        configJson['PMC_Config']['Speeds'] = {}
        
        ipField = self.ids['ip_addr_txt']
        configJson['PMC_Config']['Connection']['IP_Address'] = self.ip_addr_prop
        
        portField = self.ids['port_uint']
        configJson['PMC_Config']['Connection']['Port'] = portField.text
        
        fanSpeedField = self.ids['fan_speed_uint']
        configJson['PMC_Config']['Speeds']['Fan'] = fanSpeedField.text
        
        homeSpeedField = self.ids['home_speed_uint']
        configJson['PMC_Config']['Speeds']['Homing'] = homeSpeedField.text
        
        relativeSpeedField = self.ids['rel_mv_speed_flt']
        configJson['PMC_Config']['Speeds']['RelativeMove'] = relativeSpeedField.text
        
        absoluteSpeedField = self.ids['abs_mv_speed_flt']
        configJson['PMC_Config']['Speeds']['AbsoluteMove'] = absoluteSpeedField.text
        
        configJsonObject = json.dumps(configJson, indent=4)
        f.write(configJsonObject)
        f.close()
        TerminalWidget.addMessage('Saved config file')

        
# class PMC_Config_App(App):
#     def build(self):
#         return PMC_Config_GUI()


# if __name__ == "__main__":
#     PMC_Config_App().run()