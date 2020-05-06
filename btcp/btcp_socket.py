from btcp.btcp_segment import *
from btcp.lossy_layer import LossyLayer
from btcp.constants import *

RECEIVE_BUFFER_SIZE = 100

class BTCPSocket:

    def __init__(self, window, timeout):
        self._window = window
        self._rwindow = 0
        self._acknum = 0
        self._seqnum = 0
        self._timeout = timeout
        self.rbuffer = []
        self.status = 0 #0=nothing, 1 = client SYN sent, 2 = Server responded, 3 = Fully connected
        self._lossy_layer = None

    def create_data_segments(self, data):

        pass

    # Send data originating from the application in a reliable way to the server
    def send(self, data):
        segments = self.create_data_segments(data)

        if self._window > 0:
            pass
    
    # Send any incoming data to the application layer
    def recv(self, segment):
        if (self.in_cksum(segment)==segment.checksum and segment.seqnumber() - self._acknum == 1 and self.window > 0):
            self.rbuffer.append(segment.data)
            self._acknum += 1
            self._window -= 1
            acksegment = bTCPSegment().Factory()
            acksegment.setFlag(SegmentType.ACK)
            acksegment.setSequenceNumber(self._seqnum)
            acksegment.setAcknowledgementNumber(self._acknum)
            acksegment.setWindow(self._window)
            self._lossy_layer.send_segment(acksegment)
   
    def read(self):
        return self.rbuffer.pop(0)

    def read_all(self):
        buf = self.rbuffer
        self.rbuffer = []
        return buf

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
