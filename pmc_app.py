from kivy.app import App
from kivy.lang import Builder
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.core.window import Window

from terminal_widget import TerminalWidget#, TerminalInterface

Window.size = (900, 650)
Window.minimum_width, Window.minimum_height = Window.size



# Uncomment these lines to see all the messages
# from kivy.logger import Logger
# import logging
# Logger.setLevel(logging.TRACE)


from pmc_config_gui import PMC_Config_GUI
from pmc_gui import PMC_GUI

class TopLayout(GridLayout):
    pass
    # def __init__(self, **kwargs): 
    #     super().__init__(**kwargs)
    #     TerminalInterface.addMessage('test')
    #     term = self.ids['app_term']
        # TerminalInterface.registerTerminal(term)
    # term_data = StringProperty()
        

class PMC_APP(App):
    def build(self):
        return Builder.load_file('pmc.kv')
    

         

if __name__ == "__main__":
    PMC_APP().run()
    