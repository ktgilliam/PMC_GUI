import json
import numeric_widgets
from os.path import exists
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout

from kivy.core.window import Window
Window.size = (450, 600)
Window.minimum_width, Window.minimum_height = Window.size

from terminal_widget import TerminalWidget

Builder.load_file('pmc_config_gui.kv')


class PMC_Config_GUI(GridLayout):
    # pass
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
        print('Writing default config file')
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
        TerminalWidget.addMessage('Wrote default config file.')
        
    def readConfig(self):
        file_exists = exists("config.json")
        if not file_exists:
            self.writeDefaultConfig()
        f = open("config.json", "r")
        configStr = f.read()
        f.close()
        configJson = json.loads(configStr)
        
        # try:
        ipField = self.ids['ip_addr_txt']
        ipString = configJson['PMC_Config']['Connection']['IP_Address']
        if ipString == None:
            ipString = ''
        ipField.text = ipString
        
        portField = self.ids['port_uint']
        portNoInt = configJson['PMC_Config']['Connection']['Port']
        if portNoInt == None:
            portNoStr = ''
        else:
            portNoStr = str(portNoInt)
        portField.text = portNoStr
        
        fanSpeedField = self.ids['fan_speed_uint']
        fanSpeedField.text = str(configJson['PMC_Config']['Speeds']['Fan'])
        
        homeSpeedField = self.ids['home_speed_uint']
        homeSpeedField.text = str(configJson['PMC_Config']['Speeds']['Homing'])
        
        relativeSpeedField = self.ids['rel_mv_speed_flt']
        relativeSpeedField.text = str(configJson['PMC_Config']['Speeds']['RelativeMove'])
        
        absoluteSpeedField = self.ids['abs_mv_speed_flt']
        absoluteSpeedField.text = str(configJson['PMC_Config']['Speeds']['AbsoluteMove'])
            
        # except:
        #     print('Invalid Config File')
    
    def saveConfig(self):
        f = open("config.json", "w")
        configJson = {}
        configJson['PMC_Config'] = {}
        configJson['PMC_Config']['Connection'] = {}
        configJson['PMC_Config']['Speeds'] = {}
        
        ipField = self.ids['ip_addr_txt']
        configJson['PMC_Config']['Connection']['IP_Address'] = ipField.text
        
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
        
        print('Saved config file')
class PMC_Config_App(App):
    def build(self):
        return PMC_Config_GUI()


if __name__ == "__main__":
    PMC_Config_App().run()