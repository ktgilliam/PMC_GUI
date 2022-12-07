import socket
# from _thread import *
# import threading

import json
from enum import IntEnum
from terminal_widget import TerminalWidget, MessageType


class ControlMode(IntEnum):
    STOP = 0
    RELATIVE = 1
    ABSOLUTE = 2

class MoveTypes(IntEnum):
    ABSOLUTE = 0
    RELATIVE = 1

class UNIT_TYPES(IntEnum):
    ENGINEERING = 0
    STEPS_PER_SEC = 1
    
class AXIS(IntEnum):
    TIP = 0
    TILT = 1
    FOCUS = 2
    

        

class PrimaryMirrorControl:
    
    _controlMode = ControlMode.STOP
    _isHomed = False
    _connected = False
    _connection = (0,0)
    
    def sendMessage(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                err = s.connect(self._connection)
                s.sendall(message.encode('utf-8')) 
                data = s.recv(1024)
                s.close()
            except socket.error as e:
                TerminalWidget.addMessage(e.strerror, MessageType.ERROR)
                return
            except Exception as e:
                TerminalWidget.addMessage(f"Unexpected {e=}, {type(e)=}", MessageType.ERROR)
                return
            
            replyStr = data.decode()
            # print(f"Received {replyStr!r}")
            return replyStr
        
    def SetMoveSpeed(self, moveSpeed, units=UNIT_TYPES.ENGINEERING):
        moveSpeedJson = {}
        moveSpeedJson["PMCMessage"] = {}
        moveSpeedJson["PMCMessage"]["VelUnits"] = units
        moveSpeedJson["PMCMessage"]["SetVelocity"] = moveSpeed
        replyStr = self.sendMessage(json.dumps(moveSpeedJson))
        
    def SendMoveCommand(self, size, axis, move_type):
        moveMsgJson = {}
        moveMsgJson["PMCMessage"] = {}
        if axis == AXIS.TIP:
            moveMsgJson["PMCMessage"]["SetTip"] = size
        elif axis == AXIS.TILT:
            moveMsgJson["PMCMessage"]["SetTilt"] = size
        elif axis == AXIS.FOCUS:
            moveMsgJson["PMCMessage"]["SetFocus"] = size
        moveMsgJson["PMCMessage"]["MoveType"] = move_type
        replyStr = self.sendMessage(json.dumps(moveMsgJson))
        
    def TipRelative(self,deltaPos):
        if self._connected:
            self.SendMoveCommand(deltaPos, AXIS.TIP, MoveTypes.RELATIVE)
        
    def TiltRelative(self,deltaPos):
        if self._connected:
            self.SendMoveCommand(deltaPos, AXIS.TILT, MoveTypes.RELATIVE)
        
    def FocusRelative(self,deltaPos):
        if self._connected:
            self.SendMoveCommand(deltaPos, AXIS.FOCUS, MoveTypes.RELATIVE)
        
    def TipAbsolute(self,pos):
        if self._connected:
            self.SendMoveCommand(pos, AXIS.TIP, MoveTypes.ABSOLUTE)
        
    def TiltAbsolute(self,pos):
        if self._connected:
            self.SendMoveCommand(pos, AXIS.TILT, MoveTypes.ABSOLUTE)
        
    def FocusAbsolute(self,pos):
        if self._connected:
            self.SendMoveCommand(pos, AXIS.FOCUS, MoveTypes.ABSOLUTE)
            
    def HomeAll(self, homeSpeed):       
        homeMsgJson = {}
        homeMsgJson["PMCMessage"] = {}
        homeMsgJson["PMCMessage"]["FindHome"] = int(homeSpeed)
        replyStr = self.sendMessage(json.dumps(homeMsgJson))
        self._isHomed = True
        TerminalWidget.addMessage('Homing...')
        
    def Connect(self, _ip, _port):
        TerminalWidget.addMessage('Connecting...')
        self._connection = (_ip, _port)
        handshakeJson = {}
        handshakeJson["PMCMessage"] = {}
        handshakeJson["PMCMessage"]["Handshake"] = 0xDEAD
        replyStr = self.sendMessage(json.dumps(handshakeJson))
        if replyStr != None and len(replyStr) > 0:
            replyJson = json.loads(replyStr)
            if replyJson["PMCMessage"]["Handshake"] == 0xBEEF:
                self._connected = True
                TerminalWidget.addMessage('Connected!')
        return self._connected
    
    def Disonnect(self):
        TerminalWidget.addMessage('Disconnecting...')
        self._connection = (0,0)
        self._connected = False
    

        
    def isHomed(self):
        return self._isHomed
    
