from kivy.app import App
from kivy.uix.settings import SettingsWithSidebar
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ConfigParser
from kivy.core.window import Window

Window.size = (900, 650)
Window.minimum_width, Window.minimum_height = Window.size


from json_settings import json_connection_settings, json_speed_settings
import re
import pmc_iface
import numeric_widgets
from terminal_widget import TerminalWidget

pmc = pmc_iface.PrimaryMirrorControlInterface()

# Uncomment these lines to see all the messages
# from kivy.logger import Logger
# import logging
# Logger.setLevel(logging.TRACE)

# for integrated settings panel: https://kivy.org/doc/stable/api-kivy.app.html?highlight=resize

class PMC_Config(ObjectProperty):
    def test(self):
        pass
    
class PMC_GUI(GridLayout):
    
    _tipTiltStepSize_urad = 1
    _focusStepSize_um = 1
    _currentTip = 0.0
    _currentTilt = 0.0
    _currentFocus = 0.0
    _isConnected = False
    
    ip_addr_prop = StringProperty()
    port_prop = NumericProperty()
    fan_speed_prop = StringProperty()
    home_speed_prop = StringProperty()
    rel_speed_prop = StringProperty()
    abs_speed_prop = StringProperty()
    
    
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
 
    def connectButtonPushed(self, _ip, _port):
        #term = self.ids['app_term']
        conBtn = self.ids['connect_btn']
        if not self._isConnected:
            self._isConnected = pmc.Connect(_ip, _port)
            if self._isConnected:
                self.enableRelativeControls()
                if pmc.isHomed():
                    self.enableAbsoluteControls()
                conBtn.background_color = (0,1,0,1)
                conBtn.text = 'Connected'
        else:
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

        
    def stopButtonPushed(self):
        pass
        #term = self.ids['app_term']
        TerminalWidget.addMessage('Button not assigned yet!')
                 
    def defaultButtonPushed(self):
        pass
        #term = self.ids['app_term']
        TerminalWidget.addMessage('Stop Button Pushed')
        

class PMC_APP(App):
    # ip_addr = ConfigParserProperty()
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        return Builder.load_file('pmc_gui.kv')

    def build_config(self, config):
        config.setdefaults("Connection", {"ip_addr": "localhost", "ip_port": 1883})
        config.setdefaults("Speeds", {"fan": 50, "homing": 100, "rel_move": 100, "abs_move": 100})
        return super().build_config(config)
    
    def build_settings(self, settings):
        settings.add_json_panel("Connection", self.config, data=json_connection_settings)
        settings.add_json_panel("Speeds", self.config, data=json_speed_settings)
        return super().build_settings(settings)


    def on_config_change(self, config, section, key, value):
        if section == "Connection":
            if key == "ip_addr":
                self.root.ip_addr_prop = value
            elif key == "ip_port":
                self.root.port_prop = int(value)
        elif section == "Speeds":
            if key == "fan":
                self.root.fan_speed_prop = value    
            elif key == "homing":
                self.root.home_speed_prop = value
            elif key == "rel_move":
                self.root.rel_speed_prop = value 
            elif key == "abs_move":
                self.root.abs_speed_prop = value  
        return super().on_config_change(config, section, key, value)
    
    # def load_config(self):
    #     cfg = super().load_config()
    #     tmp = cfg.get("Connection", "ip_addr")
    #     return cfg
    # def load_config(self):
    #     tmp = super().load_config()
    #     return tmp
        
if __name__ == "__main__":
    PMC_APP().run()
    