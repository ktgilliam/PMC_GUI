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


class TecControllerInterface(LFASTControllerInterface):
    
    tecsConfigsReceived = 0
    def __init__(self, msgTypeLabel="default"):
        super().__init__()
        self._messageTypeLabel = msgTypeLabel
        
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
            self.tecsConfigsReceived = 0
            
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


    def sendBlankCommand(myConnection):
        """ This routine sends just a TECCommand Json message to keep the loop in the TEC box going """
        myJsonMsg = {}
        myJsonMsg["TECCommand"] = {}
        myJsonMsgStr = json.dumps(myJsonMsg)
        txStr = myJsonMsgStr
        myConnection.sendall(txStr.encode('utf-8'))
    #    print("finished sending a blank message to TECs")
        return

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

    numtimes = 0
    def checkMessages(self, replyJson):
        # print('\n')
        self.numtimes = self.numtimes+1
        if "tecConfigList" in replyJson:
            tec_list = replyJson['tecConfigList']
            for tec in tec_list:
                self.tecsConfigsReceived = self.tecsConfigsReceived + 1
                print(str(tec['ID']) + ', '+str(tec['BRD']) + ', ' + str(tec['CHN']))
            print(str(self.tecsConfigsReceived) + " tec configs received.")
                
        pass
