import socket
import time
import datetime
from collections import deque
import trio
import json
from enum import IntEnum
from exceptiongroup import catch
import sys
from math import pi

from tec_luts import *
from lfast_ctrl_box_iface import *

default_timeout = 5
rx_buff_size = 1024

class TECConfig:
    tecNo = 0
    boxNo = 0
    boardNo = 0
    channelNo = 0
    
    def __init__(self, tecNo, boxNo, boardNo, channelNo):
        self.tecNo = tecNo
        self.boxNo = boxNo
        self.boardNo = boardNo
        self.channelNo = channelNo

    
# class TECList:
    
#     tecConfigList = None
    
#     def contains(self, tecNo):
#         for tec in self.tecConfigList:
#             if filter(tec)

class TecControllerInterface(LFASTControllerInterface):
    
    tecConfigList = []
    tecsConfigsReceived = 0
    boxId = -1
    tecConfigListChanged = trio.Event()
    
    def __init__(self, msgTypeLabel="default"):
        super().__init__()
        self._messageTypeLabel = msgTypeLabel
        
    def setBoxId(self, id):
        self.boxId = id
        
    async def setHeater(self, tec, pwmPct):
        # This routine decodes to which box, board, and channel to send the
        # heater setting.
        mapIndex = np.squeeze(np.where(BOXMAP[:,0] == tec))
        box = BOXMAP[mapIndex,1]
        board = BOXMAP[mapIndex,2]
        channel = BOXMAP[mapIndex,3]
#        print(box) print(board) print(channel)
        self.sendTecCommand(int(box), int(board), int(channel), pwmPct)
        return

    async def getHeater(self, tec):
        mapIndex = np.squeeze(np.where(BOXMAP[:,0] == tec))
        box = BOXMAP[mapIndex,1]
        board = BOXMAP[mapIndex,2]
        channel = BOXMAP[mapIndex,3]
        bdData = self.getTecByBoxBoard(int(box), int(board))
        # We now have the board's data, need to sort by channel
        # The loads may be what is slowing everything down.  Use ujson instead and that may solve it
        recvJsonMsg = json.loads(bdData)
        return recvJsonMsg[TECAlias[int(channel-1)]]
    
    async def getTecConfigFromTeensy(self):
        if self._connected:
            await self.startNewMessage()
            await self.addKvCommandPairs(SendAll=True)
            await trio.sleep(0) 
            await self.sendCommands()
            
    async def sendTecCommand(self, box, board, channel, pwmPct):
        """ This routine will send a heater setting to the TEC master board.  First it sends the board number.  Then it sends the channel number.  Then it sends the setHeater commmand with the pwmPct number which will set the heater using the previously sent board and channel number.  The master will parse out the data to the appropriate card in the box depending on boards number """
        await self.addKvCommandPairs(Board=int(board), Channel=int(channel-1), setHeater=float(pwmPct))
        await trio.sleep(0)
        await self.sendCommands()  
        # myJsonMsg = {}
        # myJsonMsg["TECCommand"] = {}
        # myJsonMsg["TECCommand"]["Board"] = board
        # myJsonMsg["TECCommand"]["Channel"] = channel-1 # Channels are 0 index
        # myJsonMsg["TECCommand"]["setHeater"] = pwmPct
        # myJsonMsgStr = json.dumps(myJsonMsg)
        # txStr = myJsonMsgStr
        # enc_txStr = txStr.encode('utf-8')
        # if (box == 1):
        #     sent_size = self.connectionA.sendall(enc_txStr)
        # if (box == 2):
        #     sent_size = self.connectionB.sendall(enc_txStr)

    async def getTecByBoxBoard(self, box, board):
        """ This routine will keep getting data from the socket connection until there is a termination character.  The termination character is x """
        # Need to ask for data from the TEC box
        await self.addKvCommandPairs(Board=int(board), Channel=int(channel-1), setHeater=float(pwmPct))
        myJsonMsg = {}
        myJsonMsg["TECCommand"] = {}
        myJsonMsg["TECCommand"]["GetTECByBoard"] = board
        myJsonMsgStr = json.dumps(myJsonMsg)
        txStr = myJsonMsgStr
        if (box == 1):
            self.connectionA.sendall(txStr.encode('utf-8'))
            # now let's receive the stuff
            recvBuf = b''
            recvComplete = False
            while (recvComplete == False):
                try:
#                    print("Time A recv")
#                    start = time.time()
                    data = self.connectionA.recv(512)
#                    end = time.time()
#                    print(end - start)
                    recvBuf += data
                    if data[-1] == 0:
                        recvComplete = True
                except TimeoutError:
                    recvComplete = True

        if (box == 2):
            self.connectionB.sendall(txStr.encode('utf-8'))
            # now let's receive the stuff
            recvBuf = b''
            recvComplete = False
            while (recvComplete == False):
                try:
#                    print("Time B recv")
#                    start = time.time()
                    data = self.connectionB.recv(512)
#                    end = time.time()
#                    print(end - start)
                    recvBuf += data
                    if data[-1] == 0:
                        recvComplete = True
                except TimeoutError:
                    recvComplete = True
                
        recvStr = recvBuf[:-1].decode('utf-8')
#        self.closeTec()

        return recvStr
    
    @staticmethod
    def getTecList():
        TecControllerInterface.tecConfigList.sort(key=lambda x: x.tecNo, reverse=False)
        TecControllerInterface.tecConfigListChanged = trio.Event()
        return TecControllerInterface.tecConfigList
    

    # numtimes = 0
    async def checkMessages(self, replyJson):
        # print('\n')
        # self.numtimes = self.numtimes+1
        listLengthPrev = TecControllerInterface.tecsConfigsReceived
        if "tecConfigList" in replyJson:
            tec_list = replyJson['tecConfigList']
            for tec in tec_list:
                if len(TecControllerInterface.tecConfigList) > 0:
                    if any(x for x in TecControllerInterface.tecConfigList if x.tecNo == tec['ID']):
                        print('DUPLICATE TEC ID FOUND: '+str(tec['ID']))
                        continue
                TecControllerInterface.tecsConfigsReceived = TecControllerInterface.tecsConfigsReceived + 1
                newTecCfg = TECConfig(tec['ID'], self.boxId, tec['BRD'], tec['CHN'])
                TecControllerInterface.tecConfigList.append(newTecCfg)
                
        if "SentConfigs" in replyJson:
            sentReported = replyJson['SentConfigs']
            if sentReported != TecControllerInterface.tecsConfigsReceived:
                pass
            if listLengthPrev != TecControllerInterface.tecsConfigsReceived:
                TecControllerInterface.tecConfigListChanged.set()
            await trio.sleep(0)