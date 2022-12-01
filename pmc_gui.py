from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.clock import mainthread

# from collections import deque 
# kivy.require('1.0.7')
# from kivy.config import Config
# Config.set('graphics', 'width', '800')
# Config.set('graphics', 'height', '600')
# Config.set('graphics', 'resizable', False)

# Uncomment these lines to see all the messages
# from kivy.logger import Logger
# import logging
# Logger.setLevel(logging.TRACE)

Builder.load_file('pmc_gui.kv')

from kivy.core.window import Window
Window.size = (600, 500)
Window.minimum_width, Window.minimum_height = Window.size

from kivy.app import App

class TerminalWidget(GridLayout):
    term_id = ObjectProperty(None)
    label = StringProperty('your label here')
    text = StringProperty('')
    
    count = 0
    def addMessage(self, msg):
        self.count = self.count + 1
        printMsg = str(self.count) + ': ' + msg + '\n' + self.text
        self.text = printMsg

         
class PMC_GUI(GridLayout):
    @mainthread
    def doSomething(self):
        term = self.ids['app_term']
        term.addMessage("Button Pushed!")
        # for id in self.ids:
        #     print(id+'\n')

class PMC_GUI_APP(App):
    def build(self):
        return PMC_GUI()
        

if __name__ == "__main__":
    PMC_GUI_APP().run()
    