from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
import re
from datetime import datetime
import pmc_iface

pmc = pmc_iface.PrimaryMirrorControlInterface()

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

    def on_focus(self, instance, value):
        if not value:
            if len(self.text) == 0:
                self.text = '0.0'
            
    def insert_text(self, substring, from_undo=False):
        if len(substring) == 0:
            print('empty')
        cindex = self.cursor_index()
        if cindex == 0 and  (substring == '-' or substring == '+'):
            print('dash found')
            return super().insert_text(substring, from_undo=from_undo)

        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:           
            s = '.'.join( re.sub(pat, '', s) for s in substring.split('.', 1) )
        return super().insert_text(s, from_undo=from_undo)

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
        # tiltValField.text = str(self._currentTilt)
        tiltValField.text = str(round(self._currentTilt, 4))
        
        focusValField = self.ids['focus_val']
        # focusValField.text = str(self._currentFocus)
        focusValField.text = str(round(self._currentFocus, 4))

    def plusTipButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(' + Tip Button Pushed!')
        pmc.TipRelative(self._tipTiltStepSize_urad)
        self._currentTip = self._currentTip + self._tipTiltStepSize_urad
        self.updateOutputFields()
        
    def minusTipButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" - Tip Button Pushed!")
        pmc.TipRelative(-1*self._tipTiltStepSize_urad)
        self._currentTip = self._currentTip - self._tipTiltStepSize_urad
        self.updateOutputFields()
        
    def plusTiltButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" + Tilt Button Pushed!")
        pmc.TiltRelative(self._tipTiltStepSize_urad)
        self._currentTilt = self._currentTilt + self._tipTiltStepSize_urad
        self.updateOutputFields()

    def minusTiltButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" - Tilt Button Pushed!")
        pmc.TiltRelative(-1*self._tipTiltStepSize_urad)
        self._currentTilt = self._currentTilt - self._tipTiltStepSize_urad
        self.updateOutputFields()
        
    def plusFocusButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" + Focus Button Pushed!")
        pmc.FocusRelative(self._focusStepSize_um)
        self._currentFocus = self._currentFocus + self._focusStepSize_um
        self.updateOutputFields()
        
    def minusFocusButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage(" - Focus Button Pushed!")
        pmc.FocusRelative(-1*self._focusStepSize_um)
        self._currentFocus = self._currentFocus - self._focusStepSize_um
        self.updateOutputFields()
    
    def resetTipTiltStepSizeButtons(self):
        buttonFilt = re.compile('_10*uradButton')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
        
    def resetFocusStepSizeButtons(self):
        buttonFilt = re.compile('_10*umButton')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
            
    def _1uradButtonPushed(self):
        self._tipTiltStepSize_urad = 1
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_1uradButton']
        btn.background_color = (0,1,0,1)
        
    def _10uradButtonPushed(self):
        self._tipTiltStepSize_urad = 10
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_10uradButton']
        btn.background_color = (0,1,0,1)
        
    def _100uradButtonPushed(self):
        self._tipTiltStepSize_urad = 100
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_100uradButton']
        btn.background_color = (0,1,0,1)
        
    def _1000uradButtonPushed(self):
        self._tipTiltStepSize_urad = 1000
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_1000uradButton']
        btn.background_color = (0,1,0,1)
        
    def _1umButtonPushed(self):
        self._focusStepSize_um = 1
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._focusStepSize_um) + 'um')
        self.resetFocusStepSizeButtons()
        btn = self.ids['_1umButton']
        btn.background_color = (0,1,0,1)

    def _10umButtonPushed(self):
        self._focusStepSize_um = 10
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._focusStepSize_um) + 'um') 
        self.resetFocusStepSizeButtons()
        btn = self.ids['_10umButton']
        btn.background_color = (0,1,0,1)
        
    def _100umButtonPushed(self):
        self._focusStepSize_um = 100
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._focusStepSize_um) + 'um')
        self.resetFocusStepSizeButtons()
        btn = self.ids['_100umButton']
        btn.background_color = (0,1,0,1)

    def _1000umButtonPushed(self):
        self._focusStepSize_um = 1000
        term = self.ids['app_term']
        term.addMessage('Tip/Tilt Step size: ' + str(self._focusStepSize_um) + 'um')   
        self.resetFocusStepSizeButtons()
        btn = self.ids['_1000umButton']
        btn.background_color = (0,1,0,1) 
             
    def tipAbsGoButtonPushed(self):
        term = self.ids['app_term']
        tipAbsTI = self.ids['tip_abs']
        if len(tipAbsTI.text) > 0:
            self._currentTip = float(tipAbsTI.text)
            term.addMessage('Mirror Tip set to : ' + str(self._currentTip))
            self.updateOutputFields()
        
    def tiltAbsGoButtonPushed(self):
        term = self.ids['app_term']
        tiltAbsTI = self.ids['tilt_abs']
        if len(tiltAbsTI.text) > 0:
            self._currentTilt = float(tiltAbsTI.text)        
            term.addMessage('Mirror Tilt set to : ' + str(self._currentTilt))
            self.updateOutputFields()
        
    def focusAbsGoButtonPushed(self):
        term = self.ids['app_term']
        focusAbsTI = self.ids['focus_abs']
        if len(focusAbsTI.text) > 0:
            self._currentFocus = float(focusAbsTI.text)        
            term.addMessage('Mirror Focus set to : ' + str(self._currentFocus))
            self.updateOutputFields()
 
    def connectButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage('Connect Button Pushed!')
        pmc.Connect()
               
    def homingButtonPushed(self):
        term = self.ids['app_term']
        term.addMessage('Homing Button Pushed!')
        self._currentTip = 0.0
        self._currentTilt = 0.0
        self._currentFocus = 0.0
        pmc.HomeAll()
        self.updateOutputFields()
                
    def defaultButton(self):
        term = self.ids['app_term']
        term.addMessage('Button not assigned yet!')
        
        
class PMC_APP(App):
    def build(self):
        return PMC_GUI()
        

if __name__ == "__main__":
    PMC_APP().run()
    