# from threading import Thread
# import subprocess
# import sys

# from kivy.app import App
from kivy.lang import Builder
# from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.widget import Widget

import re

import pmc_iface
# import numeric_widgets

import numeric_widgets
from terminal_widget import TerminalWidget

pmc = pmc_iface.PrimaryMirrorControlInterface()

# mainWindow = 
Builder.load_file('pmc_gui.kv')

    
class PMC_GUI(TabbedPanelItem):
    
    _tipTiltStepSize_urad = 1
    _focusStepSize_um = 1
    _currentTip = 0.0
    _currentTilt = 0.0
    _currentFocus = 0.0
    _isConnected = False
    
    # def build(self):
    #     return Builder.load_file('pmc_gui.kv')
        
    def updateOutputFields(self):
        tipValField = self.ids['tip_val']
        tipValField.text = str(round(self._currentTip, 4))
        
        tiltValField = self.ids['tilt_val']
        # tiltValField.text = str(self._currentTilt)
        tiltValField.text = str(round(self._currentTilt, 4))
        
        focusValField = self.ids['focus_val']
        # focusValField.text = str(self._currentFocus)
        focusValField.text = str(round(self._currentFocus, 4))
        
    def enableRelativeControls(self):
        buttonFilt = re.compile('do_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = False
            
    def enableAbsoluteControls(self):
        buttonFilt = re.compile('go_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = False
            
    def disableControls(self):
        buttonFilt = re.compile('[d|g]o_[a-z\_]+_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.disabled = True
             
    def resetTipTiltStepSizeButtons(self):
        buttonFilt = re.compile('_10*urad_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
        
    def resetFocusStepSizeButtons(self):
        buttonFilt = re.compile('_10*um_btn')
        buttonList = [b for b in self.ids if buttonFilt.match(b)]
        for b in buttonList:
            btn = self.ids[b]
            btn.background_color = (1,1,1,1)
            
    def plusTipButtonPushed(self):
        TerminalWidget.addMessage(' Tip [+' + str(self._tipTiltStepSize_urad) + ' urad]')
        pmc.TipRelative(self._tipTiltStepSize_urad)
        self._currentTip = self._currentTip + self._tipTiltStepSize_urad
        self.updateOutputFields()
        
    def minusTipButtonPushed(self):
        #term = self.ids['app_term']
        TerminalWidget.addMessage(' Tip [-' + str(self._tipTiltStepSize_urad) + ' urad]')
        pmc.TipRelative(-1*self._tipTiltStepSize_urad)
        self._currentTip = self._currentTip - self._tipTiltStepSize_urad
        self.updateOutputFields()
        
    def plusTiltButtonPushed(self):
        #term = self.ids['app_term']
        TerminalWidget.addMessage(' Tilt [+' + str(self._tipTiltStepSize_urad) + ' urad]')
        pmc.TiltRelative(self._tipTiltStepSize_urad)
        self._currentTilt = self._currentTilt + self._tipTiltStepSize_urad
        self.updateOutputFields()

    def minusTiltButtonPushed(self):
        #term = self.ids['app_term']
        TerminalWidget.addMessage(' Tilt [-' + str(self._tipTiltStepSize_urad) + ' urad]')
        pmc.TiltRelative(-1*self._tipTiltStepSize_urad)
        self._currentTilt = self._currentTilt - self._tipTiltStepSize_urad
        self.updateOutputFields()
        
    def plusFocusButtonPushed(self):
        #term = self.ids['app_term']
        TerminalWidget.addMessage(' Focus [+' + str(self._focusStepSize_um) + ' urad]')
        pmc.FocusRelative(self._focusStepSize_um)
        self._currentFocus = self._currentFocus + self._focusStepSize_um
        self.updateOutputFields()
        
    def minusFocusButtonPushed(self):
        #term = self.ids['app_term']
        TerminalWidget.addMessage(' Focus [-' + str(self._focusStepSize_um) + ' urad]')
        pmc.FocusRelative(-1*self._focusStepSize_um)
        self._currentFocus = self._currentFocus - self._focusStepSize_um
        self.updateOutputFields()
    

            
    def _1uradButtonPushed(self):
        self._tipTiltStepSize_urad = 1
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_1urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _10uradButtonPushed(self):
        self._tipTiltStepSize_urad = 10
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_10urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _100uradButtonPushed(self):
        self._tipTiltStepSize_urad = 100
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad')
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_100urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _1000uradButtonPushed(self):
        self._tipTiltStepSize_urad = 1000
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Tip/Tilt Step size: ' + str(self._tipTiltStepSize_urad) + 'urad') 
        self.resetTipTiltStepSizeButtons()
        btn = self.ids['_1000urad_btn']
        btn.background_color = (0,1,0,1)
        
    def _1umButtonPushed(self):
        self._focusStepSize_um = 1
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')
        self.resetFocusStepSizeButtons()
        btn = self.ids['_1um_btn']
        btn.background_color = (0,1,0,1)

    def _10umButtonPushed(self):
        self._focusStepSize_um = 10
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um') 
        self.resetFocusStepSizeButtons()
        btn = self.ids['_10um_btn']
        btn.background_color = (0,1,0,1)
        
    def _100umButtonPushed(self):
        self._focusStepSize_um = 100
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')
        self.resetFocusStepSizeButtons()
        btn = self.ids['_100um_btn']
        btn.background_color = (0,1,0,1)

    def _1000umButtonPushed(self):
        self._focusStepSize_um = 1000
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Focus Step size: ' + str(self._focusStepSize_um) + 'um')   
        self.resetFocusStepSizeButtons()
        btn = self.ids['_1000um_btn']
        btn.background_color = (0,1,0,1) 
             
    def tipAbsGoButtonPushed(self):
        #term = self.ids['app_term']
        tipAbsTI = self.ids['tip_abs']
        if len(tipAbsTI.text) > 0:
            self._currentTip = float(tipAbsTI.text)
            TerminalWidget.addMessage('Mirror Tip set to : ' + str(self._currentTip))
            pmc.TipAbsolute(self._currentTip)
            self.updateOutputFields()
        
    def tiltAbsGoButtonPushed(self):
        #term = self.ids['app_term']
        tiltAbsTI = self.ids['tilt_abs']
        if len(tiltAbsTI.text) > 0:
            self._currentTilt = float(tiltAbsTI.text)        
            TerminalWidget.addMessage('Mirror Tilt set to : ' + str(self._currentTilt))
            pmc.TiltAbsolute(self._currentTilt)
            self.updateOutputFields()
        
    def focusAbsGoButtonPushed(self):
        #term = self.ids['app_term']
        focusAbsTI = self.ids['focus_abs']
        if len(focusAbsTI.text) > 0:
            self._currentFocus = float(focusAbsTI.text)        
            TerminalWidget.addMessage('Mirror Focus set to : ' + str(self._currentFocus))
            pmc.FocusAbsolute(self._currentFocus)
            self.updateOutputFields()
 
    def connectButtonPushed(self):
        #term = self.ids['app_term']
        conBtn = self.ids['connect_btn']
        if not self._isConnected:
            TerminalWidget.addMessage('Connecting...')
            TerminalWidget.addMessage('Connecting...')
            self._isConnected = pmc.Connect()
            if self._isConnected:
                TerminalWidget.addMessage('Connected!')
                TerminalWidget.addMessage('Connected!')
                self.enableRelativeControls()
                if pmc.isHomed():
                    self.enableAbsoluteControls()
                conBtn.background_color = (0,1,0,1)
                conBtn.text = 'Connected'
        else:
            TerminalWidget.addMessage('Disconnecting...')
            pmc.Disonnect()
            self._isConnected = False
            self.disableControls()
            conBtn.background_color = (1,0,0,1)
            conBtn.text = 'Connect'

    def homingButtonPushed(self):
        #term = self.ids['app_term']
        TerminalWidget.addMessage('Homing Button Pushed!')
        self._currentTip = 0.0
        self._currentTilt = 0.0
        self._currentFocus = 0.0
        pmc.HomeAll()
        self.enableAbsoluteControls()
        self.updateOutputFields()
        
    # def configButtonPushed(self):
    #     self.open_config_window()
        # pmc_config_app.editConfig()
        # #term = self.ids['app_term']
        # TerminalWidget.addMessage('Button not assigned yet!')
        
    def stopButtonPushed(self):
        pass
        #term = self.ids['app_term']
        TerminalWidget.addMessage('Button not assigned yet!')
                 
    def defaultButtonPushed(self):
        pass
        #term = self.ids['app_term']
        TerminalWidget.addMessage('Stop Button Pushed')
        
    # @staticmethod
    def open_config_window(self):
        tmp = 1
        # sm = app root.ids['sm']
        # Thread(target=lambda *largs: subprocess.run([sys.executable, "pmc_config_app.py"])).start()
        

