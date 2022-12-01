from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.clock import mainthread
import re
from datetime import datetime

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
Window.size = (900, 600)
Window.minimum_width, Window.minimum_height = Window.size

from kivy.app import App

class TerminalWidget(GridLayout):
    term_id = ObjectProperty(None)
    label = StringProperty('your label here')
    text = StringProperty('')
    
    # count = 0
    def addMessage(self, msg):
        # self.count = self.count + 1
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        printMsg = current_time + ':  ' + msg + '\n' + self.text
        self.text = printMsg

class FloatInput(TextInput):
    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join(
                re.sub(pat, '', s)
                for s in substring.split('.', 1)
            )
        return super().insert_text(s, from_undo=from_undo)

class PMC_GUI(GridLayout):
    @mainthread
    
    def plusTipButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" + Tip Button Pushed!")
        
    def minusTipButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" - Tip Button Pushed!")
        
    def plusTiltButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" + Tilt Button Pushed!")

    def minusTiltButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" - Tilt Button Pushed!")
        
    def plusFocusButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" + Focus Button Pushed!")
        
    def minusFocusButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" - Focus Button Pushed!")        
    
    def resetTipTiltStepSizeButtons(self):
        buttonFilt = re.compile('_10*uradButton')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
        # print('\n'.join(buttonList))
        
    def resetFocusStepSizeButtons(self):
        buttonFilt = re.compile('_10*umButton')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
            
    def _1uradButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 1 urad")
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_1uradButton']
        btn.background_color = (0,1,0,1)
        
    def _10uradButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 10 urad") 
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_10uradButton']
        btn.background_color = (0,1,0,1)
        
    def _100uradButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 100 urad")
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_100uradButton']
        btn.background_color = (0,1,0,1)

    def _1000uradButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 1000 urad") 
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_1000uradButton']
        btn.background_color = (0,1,0,1)
        
    def _1umButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 1 um")
        self.resetFocusStepSizeButtons()
        btn = self.ids['_1umButton']
        btn.background_color = (0,1,0,1)

    def _10umButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 10 um") 
        self.resetFocusStepSizeButtons()
        btn = self.ids['_10umButton']
        btn.background_color = (0,1,0,1)
        
    def _100umButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 100 um")
        self.resetFocusStepSizeButtons()
        btn = self.ids['_100umButton']
        btn.background_color = (0,1,0,1)

    def _1000umButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage("Tip/Tilt Step size: 1000 um")   
        self.resetFocusStepSizeButtons()
        btn = self.ids['_1000umButton']
        btn.background_color = (0,1,0,1) 
             
    def tipAbsGoButtonPushed(self):
        term = self.ids['app_term']
        tipAbsTI = self.ids['tip_abs_TI']
        term.addMessage('Tip value set:' + tipAbsTI.text)
        
    def tiltAbsGoButtonPushed(self):
        term = self.ids['app_term']
        tiltAbsTI = self.ids['tilt_abs_TI']
        term.addMessage('Tilt value set:' + tiltAbsTI.text)
        
    def focusAbsGoButtonPushed(self):
        term = self.ids['app_term']
        focusAbsTI = self.ids['focus_abs_TI']
        term.addMessage('Focus value set:' + focusAbsTI.text)
        
    def defaultButton(self):
        term = self.ids['app_term']
        term.addMessage(" Button not assigned yet!")
        
        
class PMC_GUI_APP(App):
    def build(self):
        return PMC_GUI()
        

if __name__ == "__main__":
    PMC_GUI_APP().run()
    