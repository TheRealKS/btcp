from btcp.btcp_segment import *
from btcp.lossy_layer import LossyLayer

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

    def create_data_segments(self, data: bytearray):
        # The size of the data is too large
        if len(data) > (MAX_SBUFFER_SIZE - len(self.sbuffer)) * PAYLOAD_SIZE:
            raise ValueError("Size of data too large")

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
        self.sbuffer.extend(self.create_data_segments(data))
        sendAll()

    def sendAll(self):
        for i in range(self._rwindow):
            if(len(self.sbuffer) > 0):
                self._lossy_layer.send_segment(self.sbuffer[i])
    
    # Send any incoming data to the application layer
    def recv(self, segment):
        if (self.cksumOK(segment) and segment.seqnumber() - self._acknum == 1 and self.window > 0):
            self.rbuffer.append(segment.data)
            self._acknum += 1
            self._window -= 1
            acksegment = bTCPSegment().Factory()
            acksegment.setFlag(SegmentType.ACK)
            acksegment.setSequenceNumber(self._seqnum)
            acksegment.setAcknowledgementNumber(self._acknum)
            acksegment.setWindow(self._window)
            self._lossy_layer.send_segment(acksegment)
   
    def recvAck(self, segment):
        self._rwindow = segment.window
        if (self.cksumOK(segment) and segment.acknumber == self.sbuffer[0].acknumber):
            self.sbuffer.pop(0)

    def read(self):
        return self.rbuffer.pop(0)

    def read_all(self):
        buf = self.rbuffer
        self.rbuffer = []
        return buf

    def cksumOK(self, segment):
        self.in_cksum(segment) == 0xffff
    
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

    # Return the Internet checksum of data
    @staticmethod
    def in_cksum(data):
        str_ = bytearray(data)
        csum = 0
        countTo = (len(str_) // 2) * 2

        for count in range(0, countTo, 2):
            thisVal = str_[count + 1] * 256 + str_[count]
            csum = csum + thisVal
            csum = csum & 0xffffffff

        if countTo < len(str_):
            csum = csum + str_[-1]
            csum = csum & 0xffffffff

        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        answer = ~csum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)

        return answer
