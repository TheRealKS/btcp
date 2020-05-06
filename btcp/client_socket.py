from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_segment import *
from os import urandom
from sys import byteorder
import asyncio

# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
        self.loop = asyncio.get_event_loop()
        self.tries = 1

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        rsegment = segment
        s = bTCPSegment()
        s.decode(segment[0])

        if self.status == 1:
            # Step 2 of handshake
            self.finish_connect(s)
            self._rwindow = s.window
            self.loop.stop()
            return

        if SegmentType.ACK in segment.flags & SegmentType.FIN in segment.flags:
            self.close()
        else:
            self.process_message(segment, rsegment)

    # Perform a three-way handshake to establish a connection
    def connect(self, first=True):
        if self.status > 1 and first:
            raise AttributeError("Attempt to establish connection when connection is already (being) established.")

        self._seqnum = int.from_bytes(urandom(2), byteorder)

        s = bTCPSegment()
        s = s.Factory() \
            .setFlag(SegmentType.SYN) \
            .setWindow(self._window) \
            .setSequenceNumber(self._seqnum)
        s = s.make()

        self._lossy_layer.send_segment(s)
        self.status = 1

        self.loop.call_later(self._timeout, self.timeout, self.connect)
        if first:
            self.loop.run_forever()

    def timeout(self, callback):
        if self.status == 1 or self.status == 4:
            if self.tries < MAX_TRIES:
                self.tries += 1
                callback(False)
            else:
                self.close()
                raise TimeoutError("Connection to server timed out after " + str(self.tries) + " tries")
        else:
            if not self.loop.is_closed() and not self.loop.is_running():
                self.loop.stop()
                self.loop.close()

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
    def disconnect(self, first=True):
        self.sendFin()
        self.tries = 1
        self.status = 4

        self.loop.call_later(self._timeout, self.timeout, self.disconnect)
        if first:
            self.loop.run_forever()


    # Sends a FIN package
    def sendFin(self):
        segment = bTCPSegment()
        segment = segment.Factory() \
            .setFlag(SegmentType.FIN) \
            .make()

        self._lossy_layer.send_segment(segment)


    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
