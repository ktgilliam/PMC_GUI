import socket
import time
from collections import deque
import trio
import json
from enum import IntEnum
from exceptiongroup import catch
import sys

class ControlMode(IntEnum):
    STOP = 0
    RELATIVE = 1
    ABSOLUTE = 2

class MoveTypes(IntEnum):
    STOPPED = 0
    RELATIVE = 1
    ABSOLUTE = 2

class UNIT_TYPES(IntEnum):
    ENGINEERING = 0
    STEPS_PER_SEC = 1
    
class AXIS(IntEnum):
    TIP = 0
    TILT = 1
    FOCUS = 2

class DIRECTION(IntEnum):
    REVERSE=-1
    FORWARD=1
    
    
# class PrimaryMirrorActionRequest():
#     def __init__(self, type, axis, value, units, unit_type=UNIT_TYPES.ENGINEERING, **kwargs): 
#         self._type = type
#         self._axis = axis
#         self._value = value
#         self._units = units
#         self.unit_type = unit_type
#         super().__init__(**kwargs)
    
    
default_timeout = 5
rx_buff_size = 1024

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
    _client_stream = None
    _streamReady = False
    _receiveBuffer = b''
    
    _outgoingDataTxChannel, _outgoingDataRxChannel = trio.open_memory_channel(0)
    _incomingDataTxChannel, _incomingDataRxChannel = trio.open_memory_channel(0)
    
    _disconnectCommandEvent = trio.Event()
    _newCommandDataEvent = trio.Event()
    
    _outgoingJsonMessage = {}
    
    def reset(self):
        self._currentTip = 0.0
        self._currentTilt = 0.0
        self._currentFocus = 0.0 
        self._isHomed = False
        self._disconnectCommandEvent = trio.Event()
        
    @staticmethod
    def handleDisconnectErrors(excgroup):
        for exc in excgroup.exceptions:
            pause = 1
            print(exc)
            
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
    
    async def startNewMessage(self):
        self._outgoingJsonMessage["PMCMessage"] = {}
        self._newCommandDataEvent = trio.Event()
        
    async def addKvCommandPairs(self, **kwargs):
        for key, val in kwargs.items():
            kvp = {key: val}
            self._outgoingJsonMessage["PMCMessage"].update(kvp)
        self._newCommandDataEvent.set()
        
    async def SetMoveSpeed(self, moveSpeed, units=UNIT_TYPES.ENGINEERING):
        await self.addKvCommandPairs(VelUnits=units, SetVelocity=moveSpeed)
            
    async def SendMoveCommand(self, size, axis, move_type):
        if axis == AXIS.TIP:
            await self.addKvCommandPairs(SetTip=size, MoveType=move_type)
        elif axis == AXIS.TILT:
            await self.addKvCommandPairs(SetTilt=size, MoveType=move_type)
        elif axis == AXIS.FOCUS:
            await self.addKvCommandPairs(SetFocus=size, MoveType=move_type)

            
    async def TipRelative(self,dir):
        if self._connected:
            self._currentTip += dir*self._tipTiltStepSize_urad
            await self.SendMoveCommand(dir*self._tipTiltStepSize_urad, AXIS.TIP, MoveTypes.RELATIVE)

    async def TiltRelative(self,dir):
        if self._connected:
            self._currentTilt += dir*self._tipTiltStepSize_urad
            await self.SendMoveCommand(dir*self._tipTiltStepSize_urad, AXIS.TILT, MoveTypes.RELATIVE)
        
    async def FocusRelative(self,dir):
        if self._connected:
            self._currentFocus += dir*self._focusStepSize_um
            await self.SendMoveCommand(dir*self._focusStepSize_um, AXIS.FOCUS, MoveTypes.RELATIVE)
        
    async def TipAbsolute(self,pos):
        if self._connected:
            self._currentTip = pos
            await self.SendMoveCommand(pos, AXIS.TIP, MoveTypes.ABSOLUTE)
        
    async def TiltAbsolute(self,pos):
        if self._connected:
            self._currentTilt = pos
            await self.SendMoveCommand(pos, AXIS.TILT, MoveTypes.ABSOLUTE)
        
    async def FocusAbsolute(self,pos):
        if self._connected:
            self._currentFocus = pos
            await self.SendMoveCommand(pos, AXIS.FOCUS, MoveTypes.ABSOLUTE)
            
    async def HomeAll(self, homeSpeed):       
        await self.startNewMessage()
        await self.addKvCommandPairs(FindHome=int(homeSpeed))
        
        self._currentTip = 0.0
        self._currentTilt = 0.0
        self._currentFocus = 0.0 
        self._isHomed = True
        
    
    async def aSendMessages(self, task_status=trio.TASK_STATUS_IGNORED):
        async with self._outgoingDataRxChannel.clone() as chan:
            print("inside aSendMessages with")
            async for message in chan:
                await self._client_stream.send_all(message.encode('utf-8'))
                print('Sent: ' + message)
                await self.startNewMessage()
            pass
        print("transmitter: connection closed")
        
            
    async def aReceiveMessages(self, task_status=trio.TASK_STATUS_IGNORED):
        if self._client_stream != None:
            async for data in self._client_stream:
                # print(data)
                # if self._disconnectCommandEvent.is_set():
                print("inside aReceiveMessages with")
                self._receiveBuffer += data
                lastByte = self._receiveBuffer[-1:]
                if lastByte == b'\x00':
                    recvStr = self._receiveBuffer.decode('utf-8')
                    async with self._incomingDataTxChannel.clone() as chan:
                        await chan.send(recvStr[:-1])
                    self._receiveBuffer = ''.encode('utf-8')
                    print('Received: '+ recvStr[:-1])
                    # await self._client_stream.aclose()
        # print("receiver: connection closed")

        # await trio.sleep(0)
        
    async def open_connection(self,  _ip, _port, timeout=default_timeout):
        self._connection = (_ip, _port)
        # try:
        with trio.fail_after(timeout):
            self._client_stream = await trio.open_tcp_stream(_ip, _port)
            
    async def startCommsStream(self, onException=handleDisconnectErrors):
        if self._client_stream != None:
            async with self._client_stream:
                with catch({ \
                    ConnectionResetError: onException, \
                        trio.BrokenResourceError: onException}):
                    async with trio.open_nursery() as nursery:
                        nursery.start_soon(self.aSendMessages)
                        nursery.start_soon(self.aReceiveMessages)
                        nursery.start_soon(self.checkMessages)
                        pass
                    # nursery.start_soon(self.testLoop)
                    
    async def testLoop(self):
        self.count = 0
        while 1:
            self.count += 1
            await trio.sleep(1)
            
            
    async def sendHandshake(self):
        await self.startNewMessage()
        await self.addKvCommandPairs(Handshake=0xDEAD)
        self.waitingForHandshake = trio.Event()
        await trio.sleep(0)
            
    async def waitForHandshakeReply(self, secondsToWait=default_timeout):
        with trio.fail_after(secondsToWait):
                # print("waiting for handshake")
                await self.waitingForHandshake.wait()
        
    async def sendPrimaryMirrorCommands(self):
        if self._newCommandDataEvent.is_set():
            async with self._outgoingDataTxChannel.clone() as outgoing:
                await outgoing.send(json.dumps(self._outgoingJsonMessage))

            print("sent something")
            await trio.sleep(0)
        else:
            # print("nothing to send")
            pass
        
    async def sendStopCommand(self):
        await self.startNewMessage()
        await self.addKvCommandPairs(Stop=0)
        async with self._outgoingDataTxChannel.clone() as outgoing:
                await outgoing.send(json.dumps(self._outgoingJsonMessage))
                
    async def checkMessages(self):   
        while 1:
            async with self._incomingDataRxChannel.clone() as incoming:
                async for replyStr in incoming:
                    if len(replyStr) > 0:
                        try:
                            replyJson = json.loads(replyStr)
                        except Exception as e:
                            self._connected = False
                            raise Exception('Handshake decode failed: ['+replyStr+']')
                        if "Handshake" in replyJson:
                            if replyJson["Handshake"] == 0xBEEF:
                                self._connected = True
                                self.waitingForHandshake.set()
                                # print("set handshake flag")
                                await trio.sleep(0)
                            else:
                                self._connected = False
                                raise Exception('Connection failed - handshake mismatch')
                        else:
                            print(replyStr)
                            await trio.sleep(0)
                    await trio.sleep(0.1)
        

            pause = 1
            # self.Disonnect()

            
    def Disconnect(self):
        self._connection = (0,0)
        self._connected = False
        self._disconnectCommandEvent.set()
        self.reset()
        
    def isConnected(self):
        return self._connected
    
    def isHomed(self):
        return self._isHomed
    
