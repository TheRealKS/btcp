from btcp.btcp_segment import *
from btcp.lossy_layer import LossyLayer
from threading import Timer

RECEIVE_BUFFER_SIZE = 100
MAX_SBUFFER_SIZE = 100  # Max size of data coming from application layer


class BTCPSocket:
    _lossy_layer: LossyLayer

    def __init__(self, window, timeout):
        self._window = window
        self._rwindow = 0
        self._acknum = 0
        self._seqnum = 0
        self._timeout = timeout
        self.rbuffer = []
        self.sbuffer = []
        self.status = 0  # 0=nothing, 1 = client SYN sent, 2 = Server responded, 3 = Fully connected
        self._lossy_layer = None
        self.loop_started = False

    def create_data_segments(self, data: bytearray):
        data = bytearray(data)
        # The size of the data is too large
        remaining = (MAX_SBUFFER_SIZE - len(self.sbuffer)) * PAYLOAD_SIZE
        if len(data) > remaining:
            raise ValueError(remaining)

        # While we can make segments the size of the max payload, do so
        segments = []
        while len(data) >= PAYLOAD_SIZE:
            segmentpayload = data[0:PAYLOAD_SIZE]
            del data[0:PAYLOAD_SIZE]

            self._seqnum += 1
            segments.append(self.create_data_segment(segmentpayload))

        # If there's still some data left, put it in a segment
        if len(data) > 0:
            self._seqnum += 1
            segments.append(self.create_data_segment(data))

        return segments

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        segments = self.create_data_segments(data)

        #put all packets in the sending buffer
        self.sbuffer.extend(segments)

        #send up to _rwindow of the new packets
        for i in range(0, min(len(segments), self._rwindow)):
            if(len(segments) > 0):
                self._lossy_layer.send_segment(segments[i])
            else:
                break

        #start timeout timer
        t = Timer(self._timeout, self.sendAll)
        t.start()

    # Send up to _rwindow packets currently in the sending buffer
    def sendAll(self):
        for i in range(self._rwindow):
            if(len(self.sbuffer) > 0):
                self._lossy_layer.send_segment(self.sbuffer[i])
            else:
                break
    
    # general behaviour of both sockets for receiving non handshake type messages
    def process_message(self, segment, rawSegment):
        if SegmentType.ACK in segment.flags:
            # Acknowledgment
            self.recv_ACK(segment, rawSegment)
        elif len(segment.flags) == 0:
            # Just a message
            self.recv_message(segment, rawSegment)
        else:
            raise ValueError("Invalid flag setting in message")

    # If the message is OK, put it in the receiving buffer, increase _acknum and reply with an ACK
    def recv_message(self, segment, rawSegment):
        if (self.cksumOK(rawSegment) and segment.seqnumber - self._acknum == 1 and self._window > 0):
            self.rbuffer.append(segment.data)
            self._acknum += 1
            self._window -= 1
            acksegment = bTCPSegment().Factory()
            acksegment.setFlag(SegmentType.ACK)
            acksegment.setSequenceNumber(self._seqnum)
            acksegment.setAcknowledgementNumber(self._acknum)
            acksegment.setWindow(self._window)
            self._lossy_layer.send_segment(acksegment.make())
   
    # The behaviour when receiving an ACK message: update the receiving window size and if the earliest 
    # unacknowledged message is the one acknowledged, remove it from the sending buffer
    def recv_ACK(self, segment, rawSegment):
        self._rwindow = segment.window
        if (self.cksumOK(rawSegment) and segment.acknumber == self.sbuffer[0].acknumber):
            self.sbuffer.pop(0)

    # Send any incoming data to the application layer
    def recv(self):
        buf = self.rbuffer
        self.rbuffer = []
        return buf

    # Checks if the checksum is as it should be
    def cksumOK(self, segment):
        return self.in_cksum(segment) == 0
    
    # Create a data packet
    def create_data_segment(self, data: bytearray):
        segment = bTCPSegment()
        segment = segment.Factory() \
            .setSequenceNumber(self._seqnum) \
            .setWindow(self._window) \
            .setChecksum(self.in_cksum) \
            .setPayload(data) \
            .make()

        return segment

    def getStatus(self):
        return self.status

    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(data):
        data = bytes(data)

        # turn into unsigned char and then add it to the sum
        sum = 0
        for i in range(0, len(data), 2):
            sum += int.from_bytes(data[i:(i + 2)], byteorder)

        # handle carries
        while (sum > 0xffff):
            sum = int(sum % 0x10000) + int(sum / 0x10000)

        # invert
        sum = 0xffff ^ sum

        return sum

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()