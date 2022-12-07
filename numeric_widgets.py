from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.properties import BoundedNumericProperty, NumericProperty, BooleanProperty, StringProperty, ObjectProperty

import re

#  Support functions

def isSignChar(s):
    if s == '-' or s == '+':
        return True
    else:
        return False
    
#  Widgets
class FloatInput(TextInput):
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

