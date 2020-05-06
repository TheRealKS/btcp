from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_segment import *
from os import urandom
from sys import byteorder

# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        s = bTCPSegment()
        s.decode(segment[0])

        if self.status == 1:
            # Step 2 of handshake
            self.finish_connect(s)
            self._rwindow = s.window
            return

        if SegmentType.ACK in segment.flags & SegmentType.FIN in segment.flags:
            # Disconnected
            pass
        else:
            self.process_message(segment)

    # Perform a three-way handshake to establish a connection
    def connect(self):
        if self.status > 0:
            raise AttributeError("Attempt to establish connection when connection is already (being) established.")

        self._seqnum = int.from_bytes(urandom(2), byteorder)

        s = bTCPSegment()
        s = s.Factory() \
            .setFlag(SegmentType.SYN) \
            .setWindow(self._window) \
            .setSequenceNumber(self._seqnum)
        s = s.make()

        super()._lossy_layer.send_segment(s)
        self.status += 1

    def finish_connect(self, server_segment):
        if self.status > 1:
            raise AttributeError("Attempt to establish connection when connection is already (being) established.")

        self._seqnum += 1
        self._acknum = server_segment.seqnumber + 1

        s = bTCPSegment()
        s = s.Factory() \
            .setFlag(SegmentType.ACK) \
            .setSequenceNumber(self._seqnum) \
            .setAcknowledgementNumber(self._acknum) \
            .setWindow(self._window)

        self._lossy_layer.send_segment(s.make())
        self.status = 3

    # Perform a handshake to terminate a connection
    def disconnect(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
