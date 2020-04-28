import socket
from btcp.lossy_layer import LossyLayer
from btcp.btcp_socket import BTCPSocket
from btcp.constants import *
from btcp.btcp_segment import *
from btcp.segment_type import  *

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
            newsegment = bTCPSegment().Factory()
            newsegment.setFlag(SegmentType.SYN)
            newsegment.setFlag(SegmentType.ACK)
            newsegment.setSequenceNumber(client_segment.seqnumber + 1)
            newsegment.setAcknowledgementNumber(client_segment.acknumber + 1)

            self._lossy_layer.send_segment(newsegment.make())
            self.status = 2

    # Send any incoming data to the application layer
    def recv(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()