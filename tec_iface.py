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
    
#     async def setHeater(self, tec, pwmPct):
#         # This routine decodes to which box, board, and channel to send the
#         # heater setting.
#         mapIndex = np.squeeze(np.where(BOXMAP[:,0] == tec))
#         box = BOXMAP[mapIndex,1]
#         board = BOXMAP[mapIndex,2]
#         channel = BOXMAP[mapIndex,3]
# #        print(box) print(board) print(channel)
#         self.sendTecCommand(int(box), int(board), int(channel), pwmPct)
#         return

    # async def getHeater(self, tec):
    #     mapIndex = np.squeeze(np.where(BOXMAP[:,0] == tec))
    #     box = BOXMAP[mapIndex,1]
    #     board = BOXMAP[mapIndex,2]
    #     channel = BOXMAP[mapIndex,3]
    #     bdData = self.getTecByBoxBoard(int(box), int(board))
    #     # We now have the board's data, need to sort by channel
    #     # The loads may be what is slowing everything down.  Use ujson instead and that may solve it
    #     recvJsonMsg = json.loads(bdData)
    #     return recvJsonMsg[TECAlias[int(channel-1)]]
    
    async def getTecConfigFromTeensy(self):
        if self._connected:
            await self.startNewMessage()
            await self.addKvCommandPairs(SendAll=True)
            await trio.sleep(0) 
            await self.addCommandsToOutgoing()
            
    async def sendTecCommand(self, tecNo, duty):
        """ This routine will send a heater setting to the TEC master board.  First it sends the board number.  Then it sends the channel number.  Then it sends the setHeater commmand with the pwmPct number which will set the heater using the previously sent board and channel number.  The master will parse out the data to the appropriate card in the box depending on boards number """
        if self.isConnected():
            await self.startNewMessage()
            await self.addKvCommandPairs(TECNo=tecNo, SetDuty=float(duty))
            await self.addCommandsToOutgoing()
            await trio.sleep(0)
        else:
            pass
        
    async def sendAllToZeroCommand(self):
        if self._connected:
            await self.startNewMessage()
            await self.addKvCommandPairs(AllToZero=1)
            await trio.sleep(0)
            await self.addCommandsToOutgoing() 

    
    @staticmethod
    def getTecList(box_id=-1):
        TecControllerInterface.tecConfigList.sort(key=lambda x: x.tecNo, reverse=False)
        TecControllerInterface.tecConfigListChanged = trio.Event()
        if box_id == -1:
            return TecControllerInterface.tecConfigList
        else:
            result = filter(lambda x: x.boxNo == box_id, TecControllerInterface.tecConfigList)
            filtered_list = list(result)
            return filtered_list
    
    async def checkMessages(self, replyJson):
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
            print("Sent Reported: "+str(sentReported))
            print("Actual Sent: "+str(len(TecControllerInterface.tecConfigList)))
            if sentReported != TecControllerInterface.tecsConfigsReceived:
                pass
            if listLengthPrev != TecControllerInterface.tecsConfigsReceived:
                TecControllerInterface.tecConfigListChanged.set()