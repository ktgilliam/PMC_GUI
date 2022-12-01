import json
from os.path import exists
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout

Builder.load_file('pmc_config_gui.kv')

def editConfig():
    file_exists = exists("config.json")
    if not file_exists:
        writeDefaultConfig()
        
def writeDefaultConfig():
    print('Writing default config file')
    f = open("config.json", "w")
    configJson = {}
    configJson['PMC_Config'] = {}
    configJson['PMC_Config']['FanSpeed'] = 1.2345
    configJson['PMC_Config']['HomingSpeed'] = 100
    configJson['PMC_Config']['RelativeMoveSpeed'] = 100
    configJson['PMC_Config']['AbsoluteMoveSpeed'] = 100
    configJsonObject = json.dumps(configJson, indent=4)
    f.write(configJsonObject)
    
class PMC_Config_GUI(GridLayout):
    pass

class PMC_Config_App(App):
    def build(self):
        return PMC_Config_GUI()


if __name__ == "__main__":
    PMC_Config_App().run()