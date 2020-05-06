from btcp.btcp_segment import *
from btcp.lossy_layer import LossyLayer
import asyncio

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
        self.loop = asyncio.get_event_loop()
        self.loop_started = False

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
        segments = self.create_data_segments(data)
        
        #put all packets in the sending buffer
        self.sbuffer.extend(segments)

        #start timeout timer
        self.loop.call_later(self._timeout, self.sendAll())
        if not self.loop_started:
            self.loop.run_forever()
            self.loop_started = True

        #send up to _rwindow of the new packets
        for i in range(self._rwindow):
            if(len(segments) > 0):
                self._lossy_layer.send_segment(segments[i])
            else:
                break

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
            self.recv_ACK(segment)
        elif len(segment.flags) == 0:
            # Just a message
            self.recv_message(segment, rawSegment)
        else:
            raise ValueError("Invalid flag setting in message")

    # If the message is OK, put it in the receiving buffer, increase _acknum and reply with an ACK
    def recv_message(self, segment, rawSegment):
        if (self.cksumOK(rawSegment) and segment.seqnumber() - self._acknum == 1 and self._window > 0):
            self.rbuffer.append(segment.data)
            self._acknum += 1
            self._window -= 1
            acksegment = bTCPSegment().Factory()
            acksegment.setFlag(SegmentType.ACK)
            acksegment.setSequenceNumber(self._seqnum)
            acksegment.setAcknowledgementNumber(self._acknum)
            acksegment.setWindow(self._window)
            self._lossy_layer.send_segment(acksegment)
   
    # The behaviour when receiving an ACK message: update the receiving window size and if the earliest 
    # unacknowledged message is the one acknowledged, remove it from the sending buffer
    def recv_ACK(self, segment):
        self._rwindow = segment.window
        if (self.cksumOK(segment) and segment.acknumber == self.sbuffer[0].acknumber):
            self.sbuffer.pop(0)

    # Send any incoming data to the application layer
    def recv(self):
        buf = self.rbuffer
        self.rbuffer = []
        return buf

    # Checks if the checksum is as it should be
    def cksumOK(self, segment):
        return self.in_cksum(segment) == 0xffff
    
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
    # computes the Internet checksum
    def in_cksum(self, data):
        #add padding if data is odd
        if(len(data)%2 != 0):
            data = data + b'\0'

        #turn into unsigned char and then add it to the sum
        sum = int(0)
        for i in range(int(len(data)/2)):
            sum += struct.unpack('!H', data[i*2:(i*2)+2])[0]

        #handle carries
        while(sum > (2**16) - 1):
            sum = int(sum % (2**16)) + int(sum / (2**16))

        #invert
        sum = 0xffff ^ sum

        return sum 
    
    # Clean up any state
    def close(self):
        self.loop.close()
        self._lossy_layer.destroy()