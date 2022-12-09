import socket
import time
from collections import deque
import trio
import json
from enum import IntEnum
from terminal_widget import TerminalWidget, MessageType
import sys

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
    
    _tipTiltStepSize_urad = 1
    _focusStepSize_um = 1
    _currentTip = 0.0
    _currentTilt = 0.0
    _currentFocus = 0.0
    
    _controlMode = ControlMode.STOP
    _isHomed = False
    _connected = False
    _connection = (0,0)
    
    receiveBuffer = []
    receiveStrings = deque([])
    transmitStrings = deque([])
    # replyLock = threading.Lock()
    _receiveLock = trio.Lock()
    _transmitLock = trio.Lock()
    
    # _controlLock = threading.Lock()
    
    def reset(self):
        self._currentTip = 0.0
        self._currentTilt = 0.0
        self._currentFocus = 0.0 
        self.isHomed = False
        
    def setTipTiltStepSize(self, val):
        self._tipTiltStepSize_urad = val
        
    def setFocusStepSize(self, val):
        self._focusStepSize_um = val          
    
    def getCurrentTip(self):
        return self._currentTip
    
    def getCurrentTilt(self):
        return self._currentTilt
    
    def getCurrentFocus(self):
        return self._currentFocus
    
    

        
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


    def syncSendMessage(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # self.replyLock.acquire()
                s.settimeout(3)
                # await trio.sleep(0)
                err = s.connect(self._connection)
                # time.sleep(1)
                s.sendall(message.encode('utf-8')) 
                time.sleep(1)
                data = s.recv(1024)
                replyStr = data.decode()
                print(f"Received {replyStr!r}")
                s.close()
            except socket.error as e:
                # TerminalWidget.addMessage(e.strerror, MessageType.ERROR)
                TerminalWidget.addMessage(f"Socket {e=}, {type(e)=}", MessageType.ERROR)
                return
            except Exception as e:
                TerminalWidget.addMessage(f"Unexpected {e=}, {type(e)=}", MessageType.ERROR)
                return
            
            self.receiveStrings.append(replyStr[0:-1])
            # self.replyLock.release()


    async def aSendMessages(self, client_stream):
        self._transmitLock.acquire()
        if len(self.transmitStrings) > 0:
            message = self.transmitStrings.pop()
            await client_stream.send_all(message)
            await trio.sleep(0)
        self._transmitLock.release()
        
    async def aReceiveMessages(self, client_stream):
        self._receiveLock.acquire()
        async for data in client_stream:
            self.receiveBuffer.append(data)
            recvStr = data.decode(self.receiveBuffer)
            self.receiveStrings.append(recvStr)
        self._receiveLock.release()
        
    async def serviceTcpComms(self):
        client_stream = await trio.open_tcp_stream(self._connection)
        async with client_stream:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(self.aSendMessages, client_stream)
                nursery.start_soon(self.aReceiveMessages, client_stream)
                
    async def sendHandshake(self, _ip, _port):
        self._connection = (_ip, _port)
        handshakeJson = {}
        handshakeJson["PMCMessage"] = {}
        handshakeJson["PMCMessage"]["Handshake"] = 0xDEAD
        with self._transmitLock:
            self.transmitStrings.append(json.dumps(handshakeJson))        
        await self.serviceTcpComms()
        
    async def checkMessages(self):    
        self._receiveLock.acquire()
        if len(self.receiveStrings) > 0:
            replyStr = self.receiveStrings.popleft()
            if len(replyStr) > 0:
                try:
                    replyJson = json.loads(replyStr)
                    if replyJson["Handshake"] == 0xBEEF:
                        TerminalWidget.addMessage('Connected!', MessageType.GOOD_NEWS)
                        self._connected = True
                    else:
                        self._connected = False
                        TerminalWidget.addMessage('Connection failed - handshake mismatch')
                except Exception as e:
                    self._connected = False
                    TerminalWidget.addMessage('Handshake decode failed: ['+replyStr+']')
                finally:
                    pass
        self._receiveLock.release()
        await trio.sleep(0)
        
        
    def Disonnect(self):
        TerminalWidget.addMessage('Disconnecting...')
        self._connection = (0,0)
        self._connected = False
    
    def isConnected(self):
        return self._connected
    
    # def isConnected(self, connected):
    #     self._connected = connected
        
    def isHomed(self):
        return self._isHomed
    
