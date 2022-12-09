
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty

from kivy.lang import Builder
from datetime import datetime
from enum import Enum

from collections import deque

# import trio
import threading
class MessageType(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    IMPORTANT = 3
    GOOD_NEWS = 4

Builder.load_file('terminal_widget.kv')

class TerminalWidget(GridLayout):
    _lines = NumericProperty(0)
    term_no = NumericProperty()
    label = StringProperty('')
    text = StringProperty('')
    registered = BooleanProperty(False)
    terminal = None #TerminalWidget()
    printing_lock = threading.Lock()
    
    messagesToPrint = deque([])
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        TerminalWidget.terminal = self
        
    # @classmethod
    # def registerTerminal(term_class, t):
    #     if not term_class.registered:
    #         term_class.terminal = t
    #         term_class.registered = True
        
    @staticmethod
    def addMessage(msg, messageType=MessageType.INFO, terminal_id=0):
        print( type(msg))
        if len(msg) == 0:
            raise Exception("Empty Message.")
        if isinstance(TerminalWidget.terminal, TerminalWidget):
        # if TerminalWidget.registered:
            if messageType == MessageType.INFO:
                printStr = msg
                # printStr = '[color=ffffff]'+msg+'[/color]'
            elif messageType == MessageType.WARNING:
                printStr = '[color=ffa500]'+msg+'[/color]'
            elif messageType == MessageType.ERROR:
                printStr = '[color=ff0000]'+msg+'[/color]'
            elif messageType == MessageType.IMPORTANT:
                printStr = '[b][u]'+msg+'[/u][/b]'
            elif messageType == MessageType.GOOD_NEWS:
                printStr = '[color=00ff00]'+msg+'[/color]'
               
            terminal = TerminalWidget.terminal
            terminal.printing_lock.acquire()
            terminal._lines += 1
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            newMsgString = current_time + ':  ' + msg
            terminal.messagesToPrint.appendleft(newMsgString)
            terminal.printing_lock.release()
            
    def printMessages(self):
        # try:
        self.printing_lock.acquire()
        textToAppend = ''
        while len(self.messagesToPrint) > 0:
            textToAppend += self.messagesToPrint.pop() + '\n'
        self.text = textToAppend + self.text
        self.printing_lock.release()
        # except trio.Cancelled as e:
        #     print('Terminal printing was canceled', e)
        # finally:
        #     # when canceled, print that it finished
        #     print('Done wasting time')