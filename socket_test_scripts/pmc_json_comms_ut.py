# echo-client.py

import socket
import select

import json
import time
import math
# HOST = "127.0.0.1"  # The server's hostname or IP address
# PORT = 65432  # The port used by the server
HOST = "192.168.121.177"
# HOST = "localhost"

# HOST = "192.168.190.101"
PORT = 1883  # The port used by the server
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

tipDeg = 2
tiltDeg = 3
focusmm = 10

tipRad = tipDeg*math.pi/180
tiltRad = tiltDeg*math.pi/180


import unittest

default_timeout = 3

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
            keepGoing = False
    rxStr = rxBuff[:-1].decode('utf-8')
    print(f"Received:  {rxStr!r}")
    return rxStr   

def send(s, msg):
    txStr = msg +"\0"
    print("Sending: "+txStr)
    s.sendall(txStr.encode('utf-8'))

    
class PrimaryMirrorCommsMethods(unittest.TestCase):
    def test_handshake(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            err = s.connect((HOST, PORT))
            s.settimeout(default_timeout)
            # handshakeJson = {}
            # handshakeJson["PMCMessage"] = {}
            # handshakeJson["PMCMessage"]["Handshake"]=0xDEAD
            # handshakeMsgStr = json.dumps(handshakeJson)
            handshakeMsgStr = '{"PMCMessage": {"Handshake": 57005}}\0'
            send(s, handshakeMsgStr)
            rx = getReceived(s)
            
            rxJson = json.loads(rx)
            self.assertTrue( "Handshake" in rxJson ) 
            self.assertTrue( rxJson["Handshake"] == 0xBEEF ) 
            
    def test_setTipTilt(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            err = s.connect((HOST, PORT))
            s.settimeout(default_timeout)
            cmdStr = "{{""PMCMessage"": {{""SetTip"": {0:.4f}, ""SetTilt"": {1:.4f}, ""SetFocus"": {2:.4f}}}, ""MoveType"": 1}}}}\0"
            txStr = cmdStr.format(tipRad, tiltRad, focusmm)
            print (txStr)
            send(s, txStr)
            rx = getReceived(s)
            rxJson = json.loads(rx)
            self.assertTrue( "Handshake" in rxJson ) 
            self.assertTrue( rxJson["Handshake"] == 0xBEEF ) 
            # print("print something")
            self.assertTrue(True)
            

if __name__ == '__main__':
    unittest.main()


# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     err = s.connect((HOST, PORT))
#     # s.setblocking(0)
#     s.settimeout(20)
    
#     ### Handshake Test
#     handshakeMsgStr = json.dumps(handshakeJson)
#     txStr = handshakeMsgStr +"\0"
#     print("Sending: "+txStr)
#     s.sendall(txStr.encode('utf-8'))
    
#     rx = getReceived(s)
#     print(f"Received:  "+ rx)
#     time.sleep(1)
    
#     ### Set tip/tilt test
#     txStr = r'{"PMCMessage": {"SetTip": 10, "MoveType": 1}}'+'\0'
#     print("Sending: "+txStr)
#     s.sendall(txStr.encode('utf-8'))
    
#     rx = getReceived(s)
#     print(f"Received:  "+ rx)
#     time.sleep(1)
    
    
#     s.close()
    
