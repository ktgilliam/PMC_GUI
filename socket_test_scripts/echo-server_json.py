# echo-server.py

# from operator import truediv
from pickle import FALSE
import socket
from xml.dom.minidom import TypeInfo
import json
import time

# HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
# PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
altVal = 0.0
azVal = 0.0
# HOST = "192.168.190.101"
HOST = "localhost"
# HOST = "192.168.121.177"
PORT = 4500  # The port used by the server

print("Attempting to connect.")

mountParked = True
mountIsParking = False
parkCommandTime = time.time()


handshook = False


doPrint = False
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    # server.close()
    # server.bind((HOST, PORT))
    server.bind((HOST, PORT))
    server.listen()
    client_socket, client_address = server.accept()
    with client_socket:
        print(f"Connected by {client_address}")
        while True:
            txStr = ""
            doSend = False
            data = client_socket.recv(2048)
            if not data:
                break
            # print(data)
            dataStr = data.decode()
            print(dataStr)
            # break
            # print(msgJson["PMCMessage"])
            # print(msgJson["PMCMessage"]["Handshake"])
            if handshook == False:
                doSend = True
                msgJson = json.loads(dataStr)
                # handshakeStr = msgJson["PMCMessage"]["Handshake"]
                handshakeVal = msgJson["PMCMessage"]["Handshake"]
                # print(type(handshakeStr),"::"+handshakeStr)
                # handshakeVal = int(handshakeStr, 16)
                # print(hex(handshakeVal))
                if handshakeVal == 0xDEAD:
                    handshakeReplyJson = {}
                    handshakeReplyJson = {}
                    handshakeReplyJson["Handshake"] = 0xBEEF
                    handshook = True
                    handshakeMsgStr = json.dumps(handshakeReplyJson)
                    txStr = handshakeMsgStr+"\0"
                    client_socket.sendall(txStr.encode('utf-8'))

            else:
                
                # now = time.time()
                # msgJson = json.loads(dataStr)
                # doSend = False
                # ResponseJson = json.loads(dataStr)
                client_socket.sendall(dataStr.encode('utf-8')+b'\x00')
                # for key in msgJson["PMCMessage"].keys():
                #     print(key)
                #     ### Alt Az Request
                #     if key == "RequestAltAz":
                #         doPrint = False
                #         doSend = True
                #         altVal = altVal + 0.01
                #         azVal = azVal + 0.02
                #         ResponseJson["AltPosition"] = altVal
                #         ResponseJson["AzPosition"] = azVal
                #     ### Park Status Request
                #     elif key=="IsParked":
                #         doPrint = True
                #         doSend = True
                #         timeSinceParkCommand = now-parkCommandTime
                #         # print("###Time since park Command: "+str(timeSinceParkCommand))
                #         if mountIsParking :
                #             mountParked = (timeSinceParkCommand>3)
                #             print("Mount parked: "+str(timeSinceParkCommand>15))
                #             if mountParked:
                #                 mountIsParking = False
                #                 timeSinceParkCommand = 0
                #         ResponseJson["IsParked"] = mountParked
                #     ### Park Command
                #     elif key=="Park":
                #         doPrint = True
                #         doSend = True
                #         # mountParked = True
                #         if not mountIsParking:
                #             parkCommandTime = time.time()                     
                #             mountIsParking = True
                #         ResponseJson["Park"] = "$OK^"
                #         ResponseJson["NoDisconnect"] = "$OK^"
                #         # print(json.dumps(ResponseJson))
                #     ### Unpark Command
                #     elif key=="Unpark":
                #         doPrint = True
                #         doSend = True
                #         mountParked = False
                #         ResponseJson["Unpark"] = "$OK^"
                #     ### Tracking Status Request
                #     elif key=="TrackRate":
                #         doPrint = True
                #         doSend = True
                #         ResponseJson["TrackRate"] = 0.0
                #     ### FindHome Command
                #     elif key=="FindHome":
                #         doPrint = True
                #         doSend = True
                #         print("Homing...\n")
                #         time.sleep(2)
                #         ResponseJson["FindHome"] = "$OK^"
                #     ### slewToAltPosn Command
                #     elif key=="slewToAltPosn":
                #         doPrint = True
                #         doSend = True
                #         ResponseJson["slewToAltPosn"] = "$OK^"
                #     ### slewToAzPosn Command
                #     elif key=="slewToAzPosn":
                #         doPrint = True
                #         doSend = True
                #         ResponseJson["slewToAzPosn"] = "$OK^"
                #     ### syncAltPosn Command
                #     elif key=="syncAltPosn":
                #         doPrint = True
                #         doSend = True
                #         ResponseJson["syncAltPosn"] = "$OK^"
                #     ### syncAzPosn Command
                #     elif key=="syncAzPosn":
                #         doPrint = True
                #         doSend = True
                #         ResponseJson["syncAzPosn"] = "$OK^"
                #     elif key=="getTrackRate":
                #         doPrint = True
                #         doSend = True
                #         ResponseJson["TrackRate"] = 0.0
                #     elif key=="NoDisconnect":
                #         doPrint = True
                #         doSend = True
                #         ResponseJson["NoDisconnect"] = "$OK^"
                #     else:
                #         doPrint = True
                #         print("Unrecognized argument: "+key)
                # if doPrint:
                #     print("Received: "+dataStr)

                # if doSend:
                #     txStr=json.dumps(ResponseJson)
                #     txStr = txStr+"\0"
                #     client_socket.sendall(txStr.encode('utf-8'))
                #     if doPrint:
                #         print("Sent: "+txStr)
                # if doPrint:
                #     print("\n")
            # del data
            # print("\n")