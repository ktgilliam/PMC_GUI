import socket
# from _thread import *
# import threading

import json
from enum import Enum
from terminal_widget import TerminalWidget, MessageType


class ControlMode(Enum):
    STOP = 0
    RELATIVE = 1
    ABSOLUTE = 2
    
# print_lock = threading.Lock()
handshakeJson = {}
handshakeJson["PMCMessage"] = {}
handshakeJson["PMCMessage"]["Handshake"]=0xDEAD

def sendMessage(conn, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            err = s.connect(conn)
        except socket.error as exc:
            TerminalWidget.addMessage(exc.strerror, MessageType.ERROR)
            return
        # print("Sending: "+message)
        s.sendall(message.encode('utf-8')) 
        data = s.recv(1024)
        s.close()
        replyStr = data.decode()
        # print(f"Received {replyStr!r}")
        return replyStr
        

class PrimaryMirrorControlInterface:
    
    _controlMode = ControlMode.STOP
    _isHomed = False
    _connected = False
    
    def TipRelative(self,steps):
        TerminalWidget.addMessage('Tip Relative: ' + str(steps))
        
    def TiltRelative(self,steps):
        TerminalWidget.addMessage('Tilt Relative: ' + str(steps))
        
    def FocusRelative(self,steps):
        TerminalWidget.addMessage('Focus Relative: ' + str(steps))
        
    def TipAbsolute(self,steps):
        TerminalWidget.addMessage('Tip Absolute: ' + str(steps))
        
    def TiltAbsolute(self,steps):
        TerminalWidget.addMessage('Tilt Absolute: ' + str(steps))
        
    def FocusAbsolute(self,steps):
        TerminalWidget.addMessage('Focus Absolute: ' + str(steps))
        
    def Connect(self, _ip, _port):
        TerminalWidget.addMessage('Connecting...')
        conn = (_ip, _port)
        handshakeMsgStr = json.dumps(handshakeJson)
        replyStr = sendMessage(conn, handshakeMsgStr)
        if replyStr != None:
            replyJson = json.loads(replyStr)
            if replyJson["PMCMessage"]["Handshake"] == 0xBEEF:
                self._connected = True
                TerminalWidget.addMessage('Connected!')
        return self._connected
    
    def Disonnect(self):
        TerminalWidget.addMessage('Disconnecting...')
        self._connected = False
    
    def HomeAll(self):
        self._isHomed = True
        TerminalWidget.addMessage('Homing')
        
    def isHomed(self):
        return self._isHomed
    
