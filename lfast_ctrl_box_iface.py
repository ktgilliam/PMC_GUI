import socket
import time
from collections import deque
import trio
import json
from enum import IntEnum
from exceptiongroup import catch
import sys
from math import pi


default_timeout = 5
rx_buff_size = 1024


class LFASTControllerInterface:  
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
    _handshakeReceived = trio.Event()
    _outgoingJsonMessage = {}
    _messageTypeLabel = "default"
    
    def __init__(self):
        pass
    
    def reset(self):
        self._disconnectCommandEvent = trio.Event()
        
    async def startNewMessage(self):
        self._outgoingJsonMessage[self._messageTypeLabel] = {}
        self._newCommandDataEvent = trio.Event()
        
    async def addKvCommandPairs(self, **kwargs):
        for key, val in kwargs.items():
            kvp = {key: val}
            self._outgoingJsonMessage[self._messageTypeLabel].update(kvp)
        self._newCommandDataEvent.set()
            
    async def sendHandshake(self):
        await self.startNewMessage()
        await self.addKvCommandPairs(Handshake=0xDEAD)
        self._handshakeReceived = trio.Event()
        await trio.sleep(0)
        await self.sendCommands()
        
    async def waitForHandshakeReply(self, secondsToWait=default_timeout):
        with trio.fail_after(secondsToWait) as cancelScope:
            self._cancelScope = cancelScope
                # print("waiting for handshake")
            await self._handshakeReceived.wait()
            
        
    async def sendCommands(self):
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
    
