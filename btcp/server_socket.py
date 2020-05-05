import socket
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.btcp_segment import *
from btcp.segment_type import  *

from os import urandom
from sys import byteorder

# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        s = bTCPSegment()
        s.decode(segment[0])

        if self.status < 3:
            self.accept(s)

    # Wait for the client to initiate a three-way handshake
    def accept(self, client_segment):
        if self.status == 3:
            raise AttributeError("Attempt to establish connection when connection is already (being) established.")

        if SegmentType.ACK in client_segment.flags:
            self.status = 3
        else:
            self._seqnum = int.from_bytes(urandom(2), byteorder)
            self._acknum = client_segment.seqnumber + 1

            newsegment = bTCPSegment().Factory()
            newsegment.setFlag(SegmentType.SYN)
            newsegment.setFlag(SegmentType.ACK)
            newsegment.setAcknowledgementNumber(self._acknum)
            newsegment.setSequenceNumber(self._seqnum)
            newsegment.setWindow(self._window)
            newsegment = newsegment.make()

            self._lossy_layer.send_segment(newsegment)
            self.status = 2

        self._rwindow = client_segment.window

    # Send any incoming data to the application layer
    def recv(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
