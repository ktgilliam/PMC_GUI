
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

import trio
class MessageType(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    IMPORTANT = 3
    GOOD_NEWS = 4

Builder.load_file('terminal_widget.kv')


class TerminalWidget(GridLayout):
    # _lines = NumericProperty(0)
    term_no = NumericProperty()
    label = StringProperty('')
    text = StringProperty('')
    registered = BooleanProperty(False)
    terminal = None #TerminalWidget()
    # _printing_lock = trio.Lock()
    
    def __init__(self, **kwargs): 
        super().__init__(**kwargs)
        TerminalWidget.terminal = self
        
            
    async def printMessages(self, printReceiveChannel):
        # if len(self.messagesToPrint) > 0:
        if printReceiveChannel != None:
            textToAppend = ''
            # async with printReceiveChannel:
            async for msg in printReceiveChannel:
                textToAppend += msg + '\n'
            self.text = textToAppend + self.text

        
class TerminalManager():
    
    # messagesToPrint = deque([])
    
    def __init__(self, terminal, nursery, **kwargs): 
        self.terminal = terminal
        self.nursery = nursery
            # nursery.start_soon(producer, send_channel)
            # nursery.start_soon(consumer, receive_channel)
        
    async def addMessage(self, msg, messageType=MessageType.INFO):
        if len(msg) == 0:
            raise Exception("Empty Message.")
        if isinstance(self.terminal, TerminalWidget):
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
               
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            newMsgString = current_time + ':  ' + printStr
            
            self.printSendChannel, self.printReceiveChannel = trio.open_memory_channel(0)
            self.nursery.start_soon(self.sendToTerminalWidget, newMsgString)
            
    async def sendToTerminalWidget(self, string):
        async with self.printSendChannel:
            await self.printSendChannel.send(string)
            
    async def updateTerminalWidget(self):
        self.nursery.start_soon(self.terminal.printMessages, self.printReceiveChannel)