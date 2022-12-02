import json
from os.path import exists
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout

from kivy.core.window import Window
Window.size = (300, 600)
Window.minimum_width, Window.minimum_height = Window.size

Builder.load_file('pmc_config_gui.kv')


class PMC_Config_GUI(GridLayout):
    # pass
    def __init__(self):
        super().__init__()
        file_exists = exists("config.json")
        if not file_exists:
            self.writeDefaultConfig()
        self.readConfig()
        
    def writeDefaultConfig(self):
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
        f.close()
        
    def readConfig(self):
        pass
    
class PMC_Config_App(App):
    def build(self):
        return PMC_Config_GUI()


if __name__ == "__main__":
    PMC_Config_App().run()