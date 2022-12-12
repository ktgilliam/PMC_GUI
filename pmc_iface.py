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
    ABSOLUTE = 0
    RELATIVE = 1

class UNIT_TYPES(IntEnum):
    ENGINEERING = 0
    STEPS_PER_SEC = 1
    
class AXIS(IntEnum):
    TIP = 0
    TILT = 1
    FOCUS = 2

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
    receiveBuffer = b'' # bytearray([])
    # receiveStrings = deque([])
    # transmitStrings = deque([])
    # replyLock = threading.Lock()
    # _controlLock = threading.Lock()
    outgoingDataTxChannel, outgoingDataRxChannel = trio.open_memory_channel(0)
    incomingDataTxChannel, incomingDataRxChannel = trio.open_memory_channel(0)
    
    _newMessageCount = 0
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
            
    async def SetMoveSpeed(self, moveSpeed, units=UNIT_TYPES.ENGINEERING):
        moveSpeedJson = {}
        moveSpeedJson["PMCMessage"] = {}
        moveSpeedJson["PMCMessage"]["VelUnits"] = units
        moveSpeedJson["PMCMessage"]["SetVelocity"] = moveSpeed
        with self._transmitLock:
            self.transmitStrings.append(json.dumps(moveSpeedJson))
        
    async def SendMoveCommand(self, size, axis, move_type):
        moveMsgJson = {}
        moveMsgJson["PMCMessage"] = {}
        if axis == AXIS.TIP:
            moveMsgJson["PMCMessage"]["SetTip"] = size
        elif axis == AXIS.TILT:
            moveMsgJson["PMCMessage"]["SetTilt"] = size
        elif axis == AXIS.FOCUS:
            moveMsgJson["PMCMessage"]["SetFocus"] = size
        moveMsgJson["PMCMessage"]["MoveType"] = move_type
        with self._transmitLock:
            self.transmitStrings.append(json.dumps(moveMsgJson))
        
    async def TipRelative(self,deltaPos):
        if self._connected:
            self.SendMoveCommand(deltaPos, AXIS.TIP, MoveTypes.RELATIVE)
        
    async def TiltRelative(self,deltaPos):
        if self._connected:
            self.SendMoveCommand(deltaPos, AXIS.TILT, MoveTypes.RELATIVE)
        
    async def FocusRelative(self,deltaPos):
        if self._connected:
            self.SendMoveCommand(deltaPos, AXIS.FOCUS, MoveTypes.RELATIVE)
        
    async def TipAbsolute(self,pos):
        if self._connected:
            self.SendMoveCommand(pos, AXIS.TIP, MoveTypes.ABSOLUTE)
        
    async def TiltAbsolute(self,pos):
        if self._connected:
            self.SendMoveCommand(pos, AXIS.TILT, MoveTypes.ABSOLUTE)
        
    async def FocusAbsolute(self,pos):
        if self._connected:
            self.SendMoveCommand(pos, AXIS.FOCUS, MoveTypes.ABSOLUTE)
            
    async def HomeAll(self, homeSpeed):       
        homeMsgJson = {}
        homeMsgJson["PMCMessage"] = {}
        homeMsgJson["PMCMessage"]["FindHome"] = int(homeSpeed)
        replyStr = self.sendMessage(json.dumps(homeMsgJson))
        self._currentTip = 0.0
        self._currentTilt = 0.0
        self._currentFocus = 0.0 
        self._isHomed = True
        

    async def aSendMessages(self, client_stream, outgoingDataRxChannel):
        async with outgoingDataRxChannel:
            async for message in outgoingDataRxChannel:
                print('Sent: ' + message)
                await client_stream.send_all(message.encode('utf-8'))
                await trio.sleep(0)
                
    async def aReceiveMessages(self, client_stream, incomingDataTxChannel):
        async for data in client_stream:
            # print(data)
            self.receiveBuffer += data
            lastByte = self.receiveBuffer[-1:]
            if lastByte == b'\x00':
                recvStr = self.receiveBuffer.decode('utf-8')
                await incomingDataTxChannel.send(recvStr[:-1])
                self.receiveBuffer = ''.encode('utf-8')
                self._newMessageCount += 1
                print('Received: '+ recvStr[:-1])
        sys.exit()
        # await trio.sleep(0)
        
    async def connect(self,  _ip, _port, timeout=default_timeout):
        self._connection = (_ip, _port)
        # try:
        with trio.fail_after(timeout):
            self._client_stream = await trio.open_tcp_stream(_ip, _port)

    async def startCommStreams(self):
        if self._client_stream != None:
            async with self._client_stream:
                with catch({ConnectionResetError: self.handleDisconnectErrors}):
                    async with trio.open_nursery() as nursery:
                        nursery.start_soon(self.aSendMessages, self._client_stream, self.outgoingDataRxChannel.clone())
                        nursery.start_soon(self.aReceiveMessages, self._client_stream, self.incomingDataTxChannel.clone())
                        nursery.start_soon(self.checkMessages, self.incomingDataRxChannel.clone())
                        
    async def sendHandshake(self):
        handshakeJson = {}
        handshakeJson["PMCMessage"] = {}
        handshakeJson["PMCMessage"]["Handshake"] = 0xDEAD
        async with self.outgoingDataTxChannel.clone() as outgoing:
            await outgoing.send(json.dumps(handshakeJson))
            print("creating handshake flag")
            self.waitingForHandshake = trio.Event()
            await trio.sleep(0)
            
    async def waitForHandshakeReply(self, secondsToWait=default_timeout):
        with trio.fail_after(secondsToWait):
            # async with trio.open_nursery() as nursery:
                # nursery.start_soon(self.checkMessages)
                
                print("waiting for handshake")
                await self.waitingForHandshake.wait()
                print("saw handshake flag")
            # while not self._connected:
            #     # await trio.sleep(0)
            #     await self.checkMessages()
            #     pause = 1

        if not self._connected:
            self._client_stream = None
            raise TimeoutError('Did not receive handshake reply.')
        
    async def checkMessages(self, incomingDataRxChannel):   
        while 1:
            async with incomingDataRxChannel as incoming:
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
                                print("set handshake flag")
                                await trio.sleep(0)
                            else:
                                self._connected = False
                                raise Exception('Connection failed - handshake mismatch')
                    self._newMessageCount -= 1
                    await trio.sleep(0.1)
        
    def handleDisconnectErrors(self, excgroup):
        for exc in excgroup.exceptions:
            pause = 1
            self.Disonnect()

            
    def Disonnect(self):
        self._connection = (0,0)
        self._connected = False
    
    def isConnected(self):
        return self._connected
    
    def isHomed(self):
        return self._isHomed
    
