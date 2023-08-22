import socket
import time
from collections import deque
import trio
import json
from enum import IntEnum
from exceptiongroup import catch
import sys
from math import pi
import pprint

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
    _debug_mode = False
    
    def __init__(self):
        pass
    
    def reset(self):
        self._disconnectCommandEvent = trio.Event()
        
    @staticmethod
    def setDebugMode(dm):
        LFASTControllerInterface._debug_mode = dm
        
    async def startNewMessage(self):
        while self._newCommandDataEvent.is_set():
            await trio.sleep(0)
        self._outgoingJsonMessage[self._messageTypeLabel] = {}
        self._newCommandDataEvent = trio.Event()
        
    async def addKvCommandPairs(self, **kwargs):
        for key, val in kwargs.items():
            kvp = {key: val}
            self._outgoingJsonMessage[self._messageTypeLabel].update(kvp)
        self._newCommandDataEvent.set()
        pass
    
    async def sendHandshake(self):
        await self.startNewMessage()
        await self.addKvCommandPairs(Handshake=0xDEAD)
        self._handshakeReceived = trio.Event()
        await trio.sleep(0)
        await self.addCommandsToOutgoing()
        
    async def waitForHandshakeReply(self, secondsToWait=default_timeout):
        with trio.fail_after(secondsToWait) as cancelScope:
            self._cancelScope = cancelScope
                # print("waiting for handshake")
            await self._handshakeReceived.wait()
            
        
    async def addCommandsToOutgoing(self):
        if self._debug_mode:
            return
        if self._newCommandDataEvent.is_set():
            async with self._outgoingDataTxChannel.clone() as outgoing:
                await outgoing.send(json.dumps(self._outgoingJsonMessage))
            self._newCommandDataEvent = trio.Event()
            pass
        
    async def aSendMessages(self, task_status=trio.TASK_STATUS_IGNORED):
        if self._debug_mode:
            return
        async with self._outgoingDataRxChannel.clone() as chan:
            print("inside aSendMessages with")
            async for message in chan:
                await self._client_stream.send_all(message.encode('utf-8'))
                await trio.sleep(0)
                print('Sent: ' + message)
                await self.startNewMessage()
            pass
        print("transmitter: connection closed")
        
    async def aReceiveMessages(self, task_status=trio.TASK_STATUS_IGNORED):
        if self._debug_mode:
            return
        if self._client_stream != None:
            async for data in self._client_stream:
                self._receiveBuffer += data
                while len(self._receiveBuffer) > 0:
                # print(self._receiveBuffer)
                    if not b'\x00' in self._receiveBuffer:
                        # haven't gotten a complete message yet
                        break
                    # pprint.pprint(self._receiveBuffer.decode('utf-8'))
                    chunks = self._receiveBuffer.split(b'\x00')
                    for chunk in chunks:
                        if len(chunk) > 0:
                            recvStr = chunk.decode('utf-8')
                            # pprint.pprint(recvStr)
                            self._receiveBuffer = self._receiveBuffer[len(chunk):]
                            async with self._incomingDataTxChannel.clone() as chan:
                                await chan.send(recvStr)
                                await trio.sleep(0)
                        else:
                            self._receiveBuffer = self._receiveBuffer[1:]   
                
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
                        nursery.start_soon(self.__checkMessages)
                    pass
                # self._client_stream = None          
            # await trio.sleep(0)
        else:
            # print("nothing to send")
            pass
        
    def interruptAnything(self):
        if(self._cancelScope != None):
            self._cancelScope.cancel()

    async def __checkMessages(self):   
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
                        else:
                            if hasattr(self, "checkMessages"):
                                await self.checkMessages(replyJson)
                            else:
                                # print(replyStr)
                                pass
                            await trio.sleep(0)
                    await trio.sleep(0)
            pass
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
    
