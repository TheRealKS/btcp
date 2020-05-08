from threading import Timer

from btcp.btcp_socket import BTCPSocket
from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_segment import *
from os import urandom
from sys import byteorder
import asyncio
import time

# bTCP client socket
# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close
class BTCPClientSocket(BTCPSocket):
    def __init__(self, window, timeout):
        super().__init__(window, timeout)
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
        self.timeouttimers = []
        self.tries = 0
        self.serverPulse = asyncio.Event()

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        rsegment = segment[0]
        s = bTCPSegment()
        s.decode(segment[0])

        if self.status == 1:
            # Step 2 of handshake
            self.serverPulse.set()
            self.status = 2
            self.finish_connect(s)
            self._rwindow = s.window
            self.serverPulse.clear()
            return

        if SegmentType.ACK in s.flags and SegmentType.FIN in s.flags:
            self.status = 0
            self.serverPulse.set()
            try:
                self._lossy_layer.destroy()
            except RuntimeError:
                pass
        else:
            self.process_message(s, rsegment)

    def connect(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait([self.b_connect()]))

    async def b_connect(self):
        await self.a_connect()

    # Perform a three-way handshake to establish a connection
    async def a_connect(self, first=True):
        if self.status > 1 and first:
            raise AttributeError("Attempt to establish connection when connection is already (being) established.")

        self.status = 1
        self.sendSYN()

        self.tries += 1
        try:
            await asyncio.wait_for(self.serverPulse.wait(), float(self._timeout))
        except asyncio.TimeoutError:
            if self.tries <= MAX_TRIES:
                print("Connection failed. Try " + str(self.tries) + "/" + str(MAX_TRIES))
                await self.a_connect(False)
            else:
                self.close()
                raise TimeoutError("Connection to server timed out after " + str(self.tries) + " tries")

    def sendSYN(self):
        self._seqnum = int.from_bytes(urandom(2), byteorder)

        s = bTCPSegment()
        s = s.Factory() \
            .setFlag(SegmentType.SYN) \
            .setWindow(self._window) \
            .setSequenceNumber(self._seqnum)
        s = s.make()

        self._lossy_layer.send_segment(s)

    def finish_connect(self, server_segment):
        if self.status > 2:
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

    def disconnect(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait([self.b_disconnect()]))

    async def b_disconnect(self):
        await self.a_disconnect()

    # Perform a handshake to terminate a connection
    async def a_disconnect(self):
        self.status = 4
        self.tries = 0
        print("Sendbuffer has " + str(len(self.sbuffer)))
        if len(self.sbuffer) == 0:
            self.sendFin()
            self.tries += 1

            try:
                await asyncio.wait_for(self.serverPulse.wait(), float(self._timeout))
            except asyncio.TimeoutError:
                if self.tries <= MAX_TRIES:
                    print("Disconnection failed. Try " + str(self.tries) + "/" + str(MAX_TRIES))
                    await self.a_disconnect()
                else:
                    self.close()
                    raise TimeoutError("Connection to server timed out after " + str(self.tries) + " tries")

    # Sends a FIN package
    def sendFin(self):
        segment = bTCPSegment()
        segment = segment.Factory() \
            .setFlag(SegmentType.FIN) \
            .make()

        self._lossy_layer.send_segment(segment)
