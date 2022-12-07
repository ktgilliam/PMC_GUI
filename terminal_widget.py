
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty

from kivy.lang import Builder
from datetime import datetime
# from threading import Lock

Builder.load_file('terminal_widget.kv')
    
class TerminalWidget(GridLayout):
    term_no = NumericProperty()
    label = StringProperty('')
    text = StringProperty('')
    registered = BooleanProperty(False)
    terminal = None #TerminalWidget()
    # printing_lock = Lock()
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        TerminalWidget.terminal = self
        
    # @classmethod
    # def registerTerminal(term_class, t):
    #     if not term_class.registered:
    #         term_class.terminal = t
    #         term_class.registered = True
        
    @staticmethod
    def addMessage(msg, terminal_id=0):
        if isinstance(TerminalWidget.terminal, TerminalWidget):
        # if TerminalWidget.registered:
            TerminalWidget.terminal.printMessage(msg)
            
    def printMessage(self, msg):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        printMsg = current_time + ':  ' + msg + '\n' + self.text
        self.text = printMsg
