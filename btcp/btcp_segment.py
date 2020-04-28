# Factory for bTCP segments

from btcp.segment_type import *
from btcp.constants import HEADER_SIZE, PAYLOAD_SIZE, SEGMENT_SIZE

from os import urandom

from btcp.btcp_segment_printer import printbTCP

from sys import byteorder

# Some indices
SEQUENCE_NUM = 0
ACK_NUM = 2
FLAGS = 4
WINDOW = 5
DATA_LENGTH = 6
CHECKSUM = 8
# Field sizes
SEQUENCE_SIZE = 2
ACK_SIZE = 2
FLAGS_SIZE = 1
WINDOW_SIZE = 1
DATA_LENGTH_SIZE = 2
CHECKSUM_SIZE = 2

class bTCPSegment:
    def __init__(self):
        # Empty fields
        self.flags = []
        self.flagint = 0
        self.seqnumber = urandom(2)
        self.acknumber = 0
        self.window = 0
        self.checksum = 0
        self.datalength = 0

        self.factory = False

    def setFlag(self, type):
        if not self.factory:
            pass

        # Throw an error if we did not get the proper type
        if not isinstance(type, SegmentType):
            raise TypeError("Type must be of type SegmentType")

        existing = self.header[FLAGS]
        mask = 1 << type.value
        new = (existing & ~mask) | mask
        self.header[FLAGS] = new

        self.flags.append(type)

        return self

    def setSequenceNumber(self, number):
        if not self.factory:
            pass

        # Setting sequence number is only allowed if SYN flag not set
        if SegmentType.SYN not in self.flags:
            self.header[SEQUENCE_NUM:SEQUENCE_NUM + SEQUENCE_SIZE] = int.to_bytes(number, SEQUENCE_SIZE, byteorder)

        return self

    def setAcknowledgementNumber(self, number):
        if not self.factory:
            pass

        self.acknumber = number
        self.header[ACK_NUM:ACK_NUM + ACK_SIZE] = int.to_bytes(number, ACK_SIZE, byteorder)
        return self

    def setWindow(self, window):
        if not self.factory:
            pass

        self.window = window
        self.header[WINDOW] = window
        return self

    def setChecksum(self, checksum):
        if not self.factory:
            pass

        self.checksum = checksum
        self.header[CHECKSUM:CHECKSUM + CHECKSUM_SIZE] = int.to_bytes(checksum, CHECKSUM_SIZE, byteorder);
        return self

    def setPayload(self, payload):
        if not self.factory:
            pass

        self.data = bytearray(payload)
        datlen = len(self.data)
        if datlen > PAYLOAD_SIZE:
            raise AttributeError("Payload too large. Length was " + str(datlen) + ", but max length is " + PAYLOAD_SIZE)

        self.datalength = datlen
        self.header[DATA_LENGTH] = datlen

        return self

    def make(self):
        if not self.factory:
            pass

        segment = self.header + self.data

        # Sanity check
        if len(segment) > SEGMENT_SIZE:
            raise AttributeError(
                "Segment too large. Length was " + str(len(segment)) + ", but max lenght is " + SEGMENT_SIZE)

        return segment

    def Factory(self):
        # Init empty array for header
        self.data = bytearray(0)
        self.header = bytearray(self.seqnumber) + bytearray(HEADER_SIZE - SEQUENCE_SIZE)

        self.factory = True
        return self

    def decode(self, rawSegment):
        header = rawSegment[0:10]
        seqnum = header[SEQUENCE_NUM:SEQUENCE_SIZE]
        self.seqnumber = int.from_bytes(seqnum, byteorder)

        acknum = header[ACK_NUM:ACK_NUM+ACK_SIZE]
        self.acknumber = int.from_bytes(acknum, byteorder)

        flags = header[FLAGS:FLAGS+FLAGS_SIZE]
        self.flags, self.flagint = self.decodeFlags(flags)

        window_ = header[WINDOW:WINDOW+WINDOW_SIZE]
        self.window = int.from_bytes(window_, byteorder)

        datlen = header[DATA_LENGTH:DATA_LENGTH+DATA_LENGTH_SIZE]
        self.datalength = int.from_bytes(datlen, byteorder)

        checksum = header[CHECKSUM:CHECKSUM+CHECKSUM_SIZE]
        self.checksum = int.from_bytes(checksum, byteorder)

    def decodeFlags(self, flags):
        number = int.from_bytes(flags, byteorder)

        flags = []

        if number & 2 != 0:
            flags.append(SegmentType.ACK)

        if number & 4 != 0:
            flags.append(SegmentType.SYN)

        if number & 5 != 0:
            flags.append(SegmentType.FIN)

        return flags, number