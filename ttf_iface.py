import socket
import time
from collections import deque
import trio
import json
from enum import IntEnum
from exceptiongroup import catch
import sys
from math import pi
from lfast_ctrl_box_iface import *

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
    

# def handleCommErrors(excgroup):
#     print("INSIDE handleCommErrors")
#     for exc in excgroup.exceptions:
#         pause = 1
#         print(exc)
# urad_per_mas = pi/648.0
# mas_per_urad = 1.0/urad_per_mas
# urad_to_arcsec = 0.2062648062471
class TipTiltFocusControlInterface(LFASTControllerInterface):
    
    _tipTiltStepSize_as = 1
    _focusStepSize_um = 0.2
    _currentTip_as = 0.0
    _currentTilt_as = 0.0
    _currentFocus_um = 0.0
    
    _controlMode = ControlMode.STOP
    _isHomed = False
    _homingComplete = trio.Event()
    _steppersEnabled = False
    
    def __init__(self, msgTypeLabel="default"):
        super().__init__()
        self._messageTypeLabel = msgTypeLabel
        
    def reset(self):
        super().reset()
        self._currentTip_as = 0.0
        self._currentTilt_as = 0.0
        self._currentFocus_um = 0.0 
        self._isHomed = False
            
    def setTipTiltStepSize(self, val):
        self._tipTiltStepSize_as = val
        
    def setFocusStepSize(self, val):
        self._focusStepSize_um = val         
    
    def getCurrentTip(self):
        return self._currentTip_as
    
    def getCurrentTilt(self):
        return self._currentTilt_as
    
    def getCurrentFocus(self):
        return self._currentFocus_um
    
    def steppersEnabled(self):
        return self._steppersEnabled
    

        
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
            self._currentTip_as += dir*self._tipTiltStepSize_as
            await self.SendRelativeMoveCommand(dir*self._tipTiltStepSize_as, AXIS.TIP)

    async def TiltRelative(self,dir):
        if self._connected:
            self._currentTilt_as += dir*self._tipTiltStepSize_as
            await self.SendRelativeMoveCommand(dir*self._tipTiltStepSize_as, AXIS.TILT)
        
    async def FocusRelative(self,dir):
        if self._connected:
            self._currentFocus_um += dir*self._focusStepSize_um
            await self.SendRelativeMoveCommand(dir*self._focusStepSize_um, AXIS.FOCUS)
    
    async def MoveAbsolute(self,tip, tilt, focus):
        if self._connected:
            await self.startNewMessage()
            self._currentTip_as = tip
            self._currentTilt_as = tilt
            self._currentFocus_um = focus
            await self.addKvCommandPairs(MoveType=MoveTypes.ABSOLUTE, SetTip=tip, SetTilt=tilt, SetFocus=focus)
            
    async def sendHomeAll(self, homeSpeed):       
        await self.startNewMessage()
        await self.addKvCommandPairs(FindHome=int(homeSpeed))
        self._currentTip_as = 0.0
        self._currentTilt_as = 0.0
        self._currentFocus_um = 0.0 
        self._homingComplete = trio.Event()
        await trio.sleep(0)
        await self.addCommandsToOutgoing()
        
    async def sendBottomFound(self):       
        await self.startNewMessage()
        await self.addKvCommandPairs(BottomFound=True)
        await trio.sleep(0)
        await self.addCommandsToOutgoing()  
        
    async def waitForHomingComplete(self, timeout=60):
        with trio.fail_after(timeout) as cancelScope:
            self._cancelScope = cancelScope
            await self._homingComplete.wait()
            print(cancelScope.cancel_called)
            print(cancelScope.cancelled_caught)
        if self._cancelScope.cancelled_caught:
            print("homing cancelled")
        self._currentTip_as = 0
        self._currentTilt_as = 0
        self._currentFocus_um = 0


    async def sendEnableSteppers(self, doEnable):
        await self.startNewMessage()
        await self.addKvCommandPairs(EnableSteppers=doEnable)
        await trio.sleep(0)
        await self.addCommandsToOutgoing()
        self._steppersEnabled = doEnable
        
    # async def sendCommands(self):
    #     if self._newCommandDataEvent.is_set():
    #         async with self._outgoingDataTxChannel.clone() as outgoing:
    #             await outgoing.send(json.dumps(self._outgoingJsonMessage))
        
    async def sendStopCommand(self):
        # await self.startNewMessage()
        await self.addKvCommandPairs(Stop=0)
        async with self._outgoingDataTxChannel.clone() as outgoing:
                await outgoing.send(json.dumps(self._outgoingJsonMessage))
        await self.addCommandsToOutgoing()
        await trio.sleep(0)
        if(self._cancelScope != None):
            self._cancelScope.cancel()
    
    def isHomed(self):
        return self._isHomed
    
    def checkMessages(self, replyJson):
        # print('\n')
        self.numtimes = self.numtimes+1
        if "HomingComplete" in replyJson:
            if replyJson["HomingComplete"] == True:
                self._homingComplete.set()
                self._isHomed = True
        elif "SteppersEnabled" in replyJson:
            self._steppersEnabled = replyJson["SteppersEnabled"]
        pass
