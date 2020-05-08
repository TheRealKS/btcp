from sys import byteorder

def printbTCP(segment):
    header = segment[0:10]
    seqnum = header[0:2]
    print("Seqnum: " + str(int.from_bytes(seqnum, byteorder)))
    acknum = header[2:4]
    print("Acknum: " + str(int.from_bytes(acknum, byteorder)))
    flags = header[4:5]
    print("Flags: " + decodeFlags(flags))
    window = header[5:6]
    print("Window: " + str(int.from_bytes(window, byteorder)))
    datlen = header[6:8]
    datlen = int.from_bytes(datlen, byteorder)
    print("Datalength: " + str(datlen))
    checksum = header[8:10]
    print("Checksum: " + str(int.from_bytes(checksum, byteorder)))

    print("Data: " + segment[10:(10 + datlen)].decode())


def decodeFlags(flags):
    intflag = int.from_bytes(flags, byteorder)
    flagstr = ""

    if (intflag == 34):
        flagstr = "ACK, FIN"
    elif (intflag == 2):
        flagstr = "ACK"
    elif (intflag == 8):
        flagstr = "SYN"
    elif (intflag == 32):
        flagstr = "FIN"
    elif (intflag == 10):
        flagstr = "ACK, SYN"

    return flagstr