from client_socket import BTCPClientSocket
from server_socket import BTCPServerSocket
import time

server = BTCPServerSocket(10, 10)
print("Server started!")

socket = BTCPClientSocket(10, 10)
socket.connect()


