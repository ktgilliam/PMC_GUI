from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.bubble import Bubble
from kivy.uix.textinput import TextInput
from kivy.properties import BoundedNumericProperty, NumericProperty, BooleanProperty, StringProperty, ObjectProperty
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.clock import Clock

import re

#  Support functions
class ToolTip(Label):
    text = StringProperty('Hello World')
    pass

def isSignChar(s):
    if s == '-' or s == '+':
        return True
    else:
        return False
    
    
class InputWithToolTip(TextInput):
    mytooltip = ToolTip()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouseover)

    def on_mouseover(self, window, pos):
        test = self.x <= pos[0] <= self.right and self.y <= pos[1] <= self.top
        if self.collide_point(*pos):
            # desired behaviour    
            pass
        
    # def show_bubble(self, *l):
    #     if not hasattr(self, 'bubb'):
    #         self.bubb = bubb = Tooltip()
    #         self.add_widget(bubb)
    #     else:
    #         values = ('left_top', 'left_mid', 'left_bottom', 'top_left',
    #             'top_mid', 'top_right', 'right_top', 'right_mid',
    #             'right_bottom', 'bottom_left', 'bottom_mid', 'bottom_right')
    #         index = values.index(self.bubb.arrow_pos)
    #         self.bubb.arrow_pos = values[(index + 1) % len(values)]
    
#  Widgets
class FloatInput(InputWithToolTip):
    
    pat = re.compile('[^0-9]') 
    def on_focus(self, instance, value):
        if not value:
            if len(self.text) == 0:
                self.text = '0.0'
            elif len(self.text) == 1 and isSignChar(self.text):
                 self.text = '0.0'
                 
    def insert_text(self, substring, from_undo=False):
        cindex = self.cursor_index()
        if cindex == 0 and isSignChar(substring):
            if len(self.text) == 0:
                insertSign = True
            else:
                if isSignChar(self.text[0]):
                    insertSign = False
                else:
                    insertSign = True
            if insertSign:
                return super().insert_text(substring, from_undo=from_undo)

        if '.' in self.text:
            s = re.sub(self.pat, '', substring)
        else:           
            s = '.'.join( re.sub(self.pat, '', s) for s in substring.split('.', 1) )
        return super().insert_text(s, from_undo=from_undo)

    def setValue(self, value):
        self.cursor_index(0)
        self.text = ''
        for ch in str(value):
            self.insert_text(ch)
            
class IntegerInput(TextInput):
    unsigned = BooleanProperty(False)
    num_digits = BoundedNumericProperty(99, min=0, max=99, errorvalue=99)
    limit_input = BooleanProperty(False)
    upper_lim = NumericProperty()
    lower_lim = NumericProperty()
    pat = re.compile('[^0-9]') 
    
    def on_focus(self, instance, value):
        if not value:
            if self.limit_input:
                rawVal = int(self.text)
                if rawVal < self.lower_lim:
                    val = self.lower_lim
                elif rawVal > self.upper_lim:
                    val = self.upper_lim
                else:
                    val = rawVal
                if not val == rawVal:
                    print('Warning: Input out of range')
                self.text = str(val)
                

               
    def insert_text(self, substring, from_undo=False):
        max_len = self.num_digits
        if self.unsigned == False:
            cindex = self.cursor_index()
            if cindex == 0 and isSignChar(substring):
                if len(self.text) == 0:
                    insertSign = True
                else:
                    if isSignChar(self.text[0]):
                        insertSign = False
                    else:
                        insertSign = True
                if insertSign:
                    return super().insert_text(substring, from_undo=from_undo)
            if len(self.text) > 0 and isSignChar(self.text[0]):
                max_len = self.num_digits+1
              
            
        if len(self.text) < max_len:
            return super().insert_text(re.sub(self.pat, '', substring), from_undo=from_undo)
