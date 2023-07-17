# echo-client.py

import socket
import select

import pprint

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

default_timeout = 2
connected = False

def getReceived(s):
    rxBuff = b''
    keepGoing = True
    while keepGoing:
        try:
            data = s.recv(1024)
            
            # print(data)
            if not data:
                # Client is done with sending.
                break
            # if data[-1] == 0:
            #     # rxBuff += ','.encode("utf-8")
            #     # rxBuff += data[1:-1]
            #     # break
            #     pass
            
            rxBuff += data
            # chunks.append(data)
        except TimeoutError:
            print("timed out.")
            keepGoing = False
    rxStr = rxBuff[:-1].decode('utf-8')
    # print(f"Received:  {rxStr!r}")
    return rxStr   

def getReceivedJson(s):
    rx = getReceived(s)
    # print(rx+'\n')
    # rx_json = json.loads(rx[1:-1])
    # return rx_json
    return rx

def send(s, msg):
    txStr = msg +"\0"
    # print("Sending: "+txStr)
    s.sendall(txStr.encode('utf-8'))

    

def test_handshake():
    result = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        err = s.connect((HOST, PORT))
        s.settimeout(default_timeout)
        handshakeMsgStr = '{"TECCommand": {"Handshake": 57005}}\0'
        send(s, handshakeMsgStr)
        rx = getReceivedJson(s)
        handshakeVal = rx["Handshake"]
        if handshakeVal == 0xbeef:
            result = True
        return result
        # return rx

def test_sendall():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        err = s.connect((HOST, PORT))
        s.settimeout(default_timeout)
        sendAllStr = '{"TECCommand": {"SendAll": 0}}\0'
        send(s, sendAllStr)
        rx = getReceivedJson(s)
        pprint.pprint(rx)
        # return rx

    
# connected = test_handshake()
connected = True
if connected:
    test_sendall()

count = 0

# while count < numToSend:
    
#     tipRad = tipDeg*math.pi/180
#     tiltRad = tiltDeg*math.pi/180
    
#     test_sendMoveCmd(MoveType, tipRad, tiltRad, focusmm)
#     time.sleep(0.1)
#     if MoveType == MoveType.RELATIVE:
#         # tipDeg += .1
#         # tiltDeg += .1
#         focusmm += 1
#     elif MoveType == MoveType.ABSOLUTE:
#         focusmm *= -1
#         time.sleep(10)
        
#     count += 1

    
# test_stop()