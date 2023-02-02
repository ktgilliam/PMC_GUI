import socket
import time
from collections import deque
import trio
import json
from enum import IntEnum
from exceptiongroup import catch
import sys
from math import pi

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

# def handleCommErrors(excgroup):
#     print("INSIDE handleCommErrors")
#     for exc in excgroup.exceptions:
#         pause = 1
#         print(exc)
urad_per_mas = pi/648.0
mas_per_urad = 1.0/urad_per_mas
# urad_to_arcsec = 0.2062648062471
class PrimaryMirrorControl:
    
    _tipTiltStepSize_mas = 1
    _focusStepSize_mm = 0.2
    _currentTip_mas = 0.0
    _currentTilt_mas = 0.0
    _currentFocus_mm = 0.0
    
    _controlMode = ControlMode.STOP
    _isHomed = False
    _connected = False
    _connection = (0,0)
    _client_stream = None
    _streamReady = False
    _receiveBuffer = b''
    _cancelScope = None
    _outgoingDataTxChannel, _outgoingDataRxChannel = trio.open_memory_channel(0)
    _incomingDataTxChannel, _incomingDataRxChannel = trio.open_memory_channel(0)
    
    _disconnectCommandEvent = trio.Event()
    _newCommandDataEvent = trio.Event()
    _homingComplete = trio.Event()
    _handshakeReceived = trio.Event()
    _outgoingJsonMessage = {}
    _steppersEnabled = False
    
    def reset(self):
        self._currentTip_mas = 0.0
        self._currentTilt_mas = 0.0
        self._currentFocus_mm = 0.0 
        self._isHomed = False
        self._disconnectCommandEvent = trio.Event()
        
    # @staticmethod
    # def handleCommErrors(excgroup):
    #     for exc in excgroup.exceptions:
    #         if isinstance(exc, trio.BrokenResourceError) or \
    #             isinstance(exc, trio.ClosedResourceError):
    #                 pass #Everything is fine, do nothing
    #         else:
    #             breakpoint()
    #             print(exc)
            
    def setTipTiltStepSize(self, val):
        self._tipTiltStepSize_mas = val
        
    def setFocusStepSize(self, val):
        self._focusStepSize_mm = val         
    
    def getCurrentTip(self):
        return self._currentTip_mas
    
    def getCurrentTilt(self):
        return self._currentTilt_mas
    
    def getCurrentFocus(self):
        return self._currentFocus_mm
    
    def steppersEnabled(self):
        return self._steppersEnabled
    
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
            
    async def SendRelativeMoveCommand(self, size, axis):
        if axis == AXIS.TIP:
            await self.addKvCommandPairs(MoveType=MoveTypes.RELATIVE, SetTip=size)
        elif axis == AXIS.TILT:
            await self.addKvCommandPairs(MoveType=MoveTypes.RELATIVE, SetTilt=size)
        elif axis == AXIS.FOCUS:
            await self.addKvCommandPairs(MoveType=MoveTypes.RELATIVE, SetFocus=size)

            
    async def TipRelative(self,dir):
        if self._connected:
            self._currentTip_mas += dir*self._tipTiltStepSize_mas
            await self.SendRelativeMoveCommand(dir*self._tipTiltStepSize_mas*urad_per_mas, AXIS.TIP)

    async def TiltRelative(self,dir):
        if self._connected:
            self._currentTilt_mas += dir*self._tipTiltStepSize_mas
            await self.SendRelativeMoveCommand(dir*self._tipTiltStepSize_mas*urad_per_mas, AXIS.TILT)
        
    async def FocusRelative(self,dir):
        if self._connected:
            self._currentFocus_mm += dir*self._focusStepSize_mm
            await self.SendRelativeMoveCommand(dir*self._focusStepSize_mm, AXIS.FOCUS)
    
    async def MoveAbsolute(self,tip, tilt, focus):
        if self._connected:
            await self.startNewMessage()
            self._currentTip_mas = tip
            self._currentTilt_mas = tilt
            self._currentFocus_mm = focus
            await self.addKvCommandPairs(MoveType=MoveTypes.ABSOLUTE, SetTip=tip*urad_per_mas, SetTilt=tilt*urad_per_mas, SetFocus=focus)
            
    async def sendHomeAll(self, homeSpeed):       
        await self.startNewMessage()
        await self.addKvCommandPairs(FindHome=int(homeSpeed))
        self._currentTip_mas = 0.0
        self._currentTilt_mas = 0.0
        self._currentFocus_mm = 0.0 
        self._homingComplete = trio.Event()
        await trio.sleep(0)
        await self.sendPrimaryMirrorCommands()
        
    async def waitForHomingComplete(self, timeout=60):
        with trio.fail_after(timeout) as cancelScope:
            self._cancelScope = cancelScope
            await self._homingComplete.wait()
            print(cancelScope.cancel_called)
            print(cancelScope.cancelled_caught)
        if self._cancelScope.cancelled_caught:
            print("homing cancelled")
        self._currentTip_mas = 0
        self._currentTilt_mas = 0
        self._currentFocus_mm = 0
            
    async def sendHandshake(self):
        await self.startNewMessage()
        await self.addKvCommandPairs(Handshake=0xDEAD)
        self._handshakeReceived = trio.Event()
        await trio.sleep(0)
        await self.sendPrimaryMirrorCommands()
        
        
    async def waitForHandshakeReply(self, secondsToWait=default_timeout):
        with trio.fail_after(secondsToWait) as cancelScope:
            self._cancelScope = cancelScope
                # print("waiting for handshake")
            await self._handshakeReceived.wait()
            
    async def sendEnableSteppers(self, doEnable):
        await self.startNewMessage()
        await self.addKvCommandPairs(EnableSteppers=doEnable)
        await trio.sleep(0)
        await self.sendPrimaryMirrorCommands()
        self._steppersEnabled = doEnable
        
    async def sendPrimaryMirrorCommands(self):
        if self._newCommandDataEvent.is_set():
            async with self._outgoingDataTxChannel.clone() as outgoing:
                await outgoing.send(json.dumps(self._outgoingJsonMessage))
                
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
                self._receiveBuffer += data
                try:
                    termIdx = self._receiveBuffer.index(b'\x00')
                    recvStr = self._receiveBuffer[0:termIdx].decode('utf-8')
                    print('Received: '+ recvStr)      
                    self._receiveBuffer = self._receiveBuffer[termIdx:-1]
                    async with self._incomingDataTxChannel.clone() as chan:
                        await chan.send(recvStr)
                except ValueError:
                    pass          
                
    async def open_connection(self,  _ip, _port, timeout=default_timeout):
        self._connection = (_ip, _port)
        # try:
        with trio.fail_after(timeout):
            self._client_stream = await trio.open_tcp_stream(_ip, _port)
            
            
    async def startCommsStream(self, handler):
        if self._client_stream != None:
            async with self._client_stream:
                with catch({ \
                    ConnectionResetError: handler, \
                        trio.BrokenResourceError: handler, \
                            trio.ClosedResourceError: handler, \
                                json.JSONDecodeError: handler}):
                    async with trio.open_nursery() as nursery:
                        nursery.start_soon(self.aSendMessages)
                        nursery.start_soon(self.aReceiveMessages)
                        nursery.start_soon(self.checkMessages)
                    pass
                # self._client_stream = None          
            # await trio.sleep(0)
        else:
            # print("nothing to send")
            pass
        
    def interruptAnything(self):
        if(self._cancelScope != None):
            self._cancelScope.cancel()
        
    async def sendStopCommand(self):
        # await self.startNewMessage()
        await self.addKvCommandPairs(Stop=0)
        async with self._outgoingDataTxChannel.clone() as outgoing:
                await outgoing.send(json.dumps(self._outgoingJsonMessage))
        await self.sendPrimaryMirrorCommands()
        await trio.sleep(0)
        if(self._cancelScope != None):
            self._cancelScope.cancel()
            # self._homingComplete.set()
        
    async def checkMessages(self):   
        while 1:
            async with self._incomingDataRxChannel.clone() as incoming:
                async for replyStr in incoming:
                    if len(replyStr) > 0:
                        replyJson = json.loads(replyStr)
                        if "Handshake" in replyJson:
                            if replyJson["Handshake"] == 0xBEEF:
                                self._connected = True
                                self._handshakeReceived.set()
                                # print("set handshake flag")
                                await trio.sleep(0)
                            else:
                                self._connected = False
                                raise Exception('Connection failed - handshake mismatch')
                        elif "HomingComplete" in replyJson:
                            print(replyStr)
                            if replyJson["HomingComplete"] == True:
                                self._homingComplete.set()
                                self._isHomed = True
                        elif "SteppersEnabled" in replyJson:
                            print(replyStr)
                            self._steppersEnabled = replyJson["SteppersEnabled"]
                        else:
                            print(replyStr)
                            await trio.sleep(0)
                    await trio.sleep(0.1)
        

            pause = 1
            # self.Disonnect()

            
    async def Disconnect(self):
        self._connection = (0,0)
        self._connected = False
        self._disconnectCommandEvent.set()
        if self._client_stream != None:
            await self._client_stream.aclose()
        self.reset()
        
    def isConnected(self):
        return self._connected
    
    def isHomed(self):
        return self._isHomed
    
