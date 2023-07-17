# echo-client.py

import socket
import select

import json
import time
import math
# HOST = "127.0.0.1"  # The server's hostname or IP address
# PORT = 65432  # The port used by the server
# HOST = "192.168.121.177"
# HOST = "localhost"
HOST = "169.254.84.177"

# HOST = "192.168.190.101"
PORT = 4500  # The port used by the server
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:




default_timeout = 10

def getReceived(s):
    rxBuff = b''
    keepGoing = True
    while keepGoing:
        try:
            data = s.recv(1024)
            rxBuff += data
            # print(data)
            if data[-1] == 0:
                keepGoing = False
        except TimeoutError:
            print("timed out.")
            keepGoing = False
    rxStr = rxBuff[:-1].decode('utf-8')
    print(f"Received:  {rxStr!r}")
    return rxStr   

def send(s, msg):
    txStr = msg +"\0"
    print("Sending: "+txStr)
    s.sendall(txStr.encode('utf-8'))

    

def test_handshake():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        err = s.connect((HOST, PORT))
        s.settimeout(default_timeout)
        handshakeMsgStr = '{"PMCMessage": {"Handshake": 57005}}\0'
        send(s, handshakeMsgStr)
        # rx = getReceived(s)
        # return rx
    
def test_sendMoveCmd(moveType, tip, tilt, focus):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        err = s.connect((HOST, PORT))
        s.settimeout(default_timeout)
        cmdStr = "{{""PMCMessage"": {{""MoveType"": {0}, ""SetTip"": {1:.4f}, ""SetTilt"": {2:.4f}, ""SetFocus"": {3:.4f}}}}}}}\0"
        txStr = cmdStr.format(moveType, tip, tilt, focus)
        send(s, txStr)
        # rx = getReceived(s)
        # return rx

def test_stop():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        err = s.connect((HOST, PORT))
        s.settimeout(default_timeout)
        handshakeMsgStr = '{"PMCMessage": {"Stop": 0}}\0'
        send(s, handshakeMsgStr)
        # rx = getReceived(s)
        # return rx

from enum import IntEnum
class MoveType(IntEnum):
    STOP = 0,
    RELATIVE = 1,
    ABSOLUTE = 2
    
MoveType = MoveType.ABSOLUTE
tipDeg = 0
tiltDeg = 0
focusmm = 0.0

if MoveType == MoveType.RELATIVE:
    numToSend = 3
    
elif MoveType == MoveType.ABSOLUTE:
    tipDeg = 0
    tiltDeg = 0
    focusmm = 5.0
    numToSend = 1
    
test_handshake()


count = 0
while count < numToSend:
    
    tipRad = tipDeg*math.pi/180
    tiltRad = tiltDeg*math.pi/180
    
    test_sendMoveCmd(MoveType, tipRad, tiltRad, focusmm)
    time.sleep(0.1)
    if MoveType == MoveType.RELATIVE:
        # tipDeg += .1
        # tiltDeg += .1
        focusmm += 1
    elif MoveType == MoveType.ABSOLUTE:
        focusmm *= -1
        time.sleep(10)
        
    count += 1

    
test_stop()