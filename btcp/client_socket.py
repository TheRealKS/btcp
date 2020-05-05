from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_segment import *


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

        if SegmentType.ACK in s.flags & SegmentType.FIN in s.flags:
            # Disconnected
            pass
        elif SegmentType.ACK in s.flags:
            # Acknowledgment
            pass
        elif len(s.flags) == 0:
            # Just a message
            pass
        else:
            raise ValueError("Invalid flag setting in message")

    # Perform a three-way handshake to establish a connection
    def connect(self):
        if self.status > 0:
            raise AttributeError("Attempt to establish connection when connection is already (being) established.")

        s = bTCPSegment()
        s = s.Factory() \
            .setFlag(SegmentType.SYN) \
            .setWindow(self._window) \
            .make()

        self._lossy_layer.send_segment(s)
        self.status += 1

    def finish_connect(self, server_segment):
        if self.status > 1:
            raise AttributeError("Attempt to establish connection when connection is already (being) established.")

        s = bTCPSegment()
        s = s.Factory() \
            .setFlag(SegmentType.ACK) \
            .setSequenceNumber(server_segment.seqnumber + 1) \
            .setAcknowledgementNumber(server_segment.acknumber + 1) \
            .setWindow(self._window) \
            .make()

        self._lossy_layer.send_segment(s)
        self.status = 3

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        segments = self.create_data_segments(data)

        if self._window > 0:

    # Perform a handshake to terminate a connection
    def disconnect(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
