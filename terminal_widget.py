from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.lang import Builder

from datetime import datetime
from threading import Lock
# from queue import Queue

Builder.load_file('terminal_widget.kv')



class TerminalMessage:
    term_id = 0
    message = ''
    
terminalList = []
    
# mgr = TerminalMessageManager

# this is not finished

class TerminalWidget(GridLayout):
    # term_id = ObjectProperty(None)
    term_no = NumericProperty()
    label = StringProperty('')
    text = StringProperty('')
    printing_lock = Lock()
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        self.term_no = len(terminalList)
        terminalList.append(self)
    
    def printMessage(self, msg):
    # def addMessage(self, msg):
        # self.count = self.count + 1
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        with self.printing_lock:
            printMsg = current_time + ':  ' + msg + '\n' + self.text
            self.text = printMsg
            
            
    @staticmethod
    def addMessage(msg, terminal_id=0):
        N = len(terminalList)
        if N > 0 and N <= terminal_id+1:
            term_obj = terminalList[terminal_id]
            term_obj.printMessage(msg)
    