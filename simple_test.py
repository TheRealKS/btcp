from client_socket import BTCPClientSocket
from server_socket import BTCPServerSocket
import time

server = BTCPServerSocket(10, 10)
print("Server started!")

socket = BTCPClientSocket(1, 10)
socket.connect()

time.sleep(2)

print("AcknumS: " + str(server._acknum))
print("AcknumC: " + str(socket._acknum))
print("SeqnumS: " + str(server._seqnum))
print("SeqnumC: " + str(socket._seqnum))
print("WindowS: " + str(server._rwindow))
print("WindowC: " + str(socket._rwindow))


