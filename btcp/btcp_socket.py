class BTCPSocket:

    def __init__(self, window, timeout):
        self._window = window
        self._rwindow = 0
        self._acknum = 0
        self._seqnum = 0
        self._timeout = timeout
        self.status = 0 #0=nothing, 1 = client SYN sent, 2 = Server responded, 3 = Fully connected

    def create_data_segments(self, data):

        pass
   
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
