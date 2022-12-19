# echo-server.py

from operator import truediv
import socket
from xml.dom.minidom import TypeInfo

# HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
# PORT = 65432  # Port to listen on (non-privileged ports are > 1023)
raVal = 0.0
deVal = 0.0
# HOST = "192.168.190.101"
HOST = "localhost"
# HOST = "192.168.121.177"
PORT = 4400  # The port used by the server

print("Attempting to connect.")

# import socket
# server = socket.socket() 
# server.bind((HOST, PORT)) 
# server.listen(4) 
# client_socket, client_address = server.accept()
# print(client_address, "has connected")

# while True:
#     recvieved_data = client_socket.recv(1024)
#     print(recvieved_data)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    # server.close()
    # server.bind((HOST, PORT))
    server.bind((HOST, PORT))
    server.listen(4)
    client_socket, client_address = server.accept()
    with client_socket:
        print(f"Connected by {client_address}")
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(data)
            client_socket.sendall(data)
            
            del data
            print("\n")