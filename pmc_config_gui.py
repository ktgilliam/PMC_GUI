import json
import numeric_widgets
from os.path import exists
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.properties import StringProperty
# from kivy.properties import AliasPro
from terminal_widget import TerminalWidget
import global_props

Builder.load_file('pmc_config_gui.kv')


class PMC_Config_GUI(TabbedPanelItem):
    # pass
    # ip_addr_prop = StringProperty()
    # port_prop = StringProperty()
    fan_speed_prop = StringProperty()
    home_speed_prop = StringProperty()
    rel_speed_prop = StringProperty()
    abs_speed_prop = StringProperty()
    _configJson = {}
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        file_exists = exists("config.json")
        if not file_exists:
            self.writeDefaultConfig()
        self.readConfigFile()
        
    def resetDefaultConfig(self):
        self.writeDefaultConfig()
        self.readConfigFile()
        
    def writeDefaultConfig(self):
        f = open("config.json", "w")
        PMC_Config_GUI._configJson['PMC_Config'] = {}
        PMC_Config_GUI._configJson['PMC_Config']['Connection'] = {}
        PMC_Config_GUI._configJson['PMC_Config']['Connection']['IP_Address'] = None
        PMC_Config_GUI._configJson['PMC_Config']['Connection']['Port'] = None
        PMC_Config_GUI._configJson['PMC_Config']['Speeds'] = {}
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['Fan'] = 50
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['Homing'] = 100
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['RelativeMove'] = 100.0
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['AbsoluteMove'] = 100.0
        configJsonObject = json.dumps(PMC_Config_GUI._configJson, indent=4)
        f.write(configJsonObject)
        f.close()
        TerminalWidget.addMessage('Wrote default config file')
        
    def readConfigFile(self):
        file_exists = exists("config.json")
        if not file_exists:
            self.writeDefaultConfig()
        f = open("config.json", "r")
        configStr = f.read()
        f.close()
        PMC_Config_GUI._configJson = json.loads(configStr)
        
        ipString = PMC_Config_GUI._configJson['PMC_Config']['Connection']['IP_Address']
        if ipString == None:
            ipString = ''
        self.ip_addr_prop = ipString
        
        portNoInt = PMC_Config_GUI._configJson['PMC_Config']['Connection']['Port']
        if portNoInt == None:
            self.port_prop = ''
        else:
            self.port_prop = str(portNoInt)
        
        self.fan_speed_prop = str(PMC_Config_GUI._configJson['PMC_Config']['Speeds']['Fan'])
        self.home_speed_prop = str(PMC_Config_GUI._configJson['PMC_Config']['Speeds']['Homing'])
        self.rel_speed_prop = str(PMC_Config_GUI._configJson['PMC_Config']['Speeds']['RelativeMove'])
        self.abs_speed_prop = str(PMC_Config_GUI._configJson['PMC_Config']['Speeds']['AbsoluteMove'])
    
    def saveConfig(self):
        f = open("config.json", "w")
        PMC_Config_GUI._configJson = {}
        PMC_Config_GUI._configJson['PMC_Config'] = {}
        PMC_Config_GUI._configJson['PMC_Config']['Connection'] = {}
        PMC_Config_GUI._configJson['PMC_Config']['Speeds'] = {}
        
        ipField = self.ids['ip_addr_txt']
        PMC_Config_GUI._configJson['PMC_Config']['Connection']['IP_Address'] = ipField.text
        
        portField = self.ids['port_uint']
        PMC_Config_GUI._configJson['PMC_Config']['Connection']['Port'] = portField.text
        
        fanSpeedField = self.ids['fan_speed_uint']
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['Fan'] = fanSpeedField.text
        
        homeSpeedField = self.ids['home_speed_uint']
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['Homing'] = homeSpeedField.text
        
        relativeSpeedField = self.ids['rel_mv_speed_flt']
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['RelativeMove'] = relativeSpeedField.text
        
        absoluteSpeedField = self.ids['abs_mv_speed_flt']
        PMC_Config_GUI._configJson['PMC_Config']['Speeds']['AbsoluteMove'] = absoluteSpeedField.text
        
        configJsonObject = json.dumps(PMC_Config_GUI._configJson, indent=4)
        f.write(configJsonObject)
        f.close()
        TerminalWidget.addMessage('Saved config file')

        @staticmethod
        def getConfigJson():
            return PMC_Config_GUI._configJson
# class PMC_Config_App(App):
#     def build(self):
#         return PMC_Config_GUI()


# if __name__ == "__main__":
#     PMC_Config_App().run()