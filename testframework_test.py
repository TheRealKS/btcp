# Koen Sauren | s1024202
# Cas Haaijman | s4372662

import unittest
import socket
import time
import sys
from btcp.server_socket import BTCPServerSocket
from btcp.client_socket import BTCPClientSocket
import string
import random
import math
import asyncio

password = ""
timeout=1
winsize=100
intf="lo"
netem_add="echo " + password + " | sudo -S tc qdisc add dev {} root netem".format(intf)
netem_change="echo " + password + " | sudo -S tc qdisc change dev {} root netem {}".format(intf,"{}")
netem_del="echo " + password + " | sudo -S tc qdisc del dev {} root netem".format(intf)

"""run command and retrieve output"""
def run_command_with_output(command, input=None, cwd=None, shell=True):
    import subprocess
    try:
      process = subprocess.Popen(command, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    except Exception as inst:
      print("problem running command : \n   ", str(command))

    [stdoutdata, stderrdata]=process.communicate(input)  # no pipes set for stdin/stdout/stdout streams so does effectively only just wait for process ends  (same as process.wait()

    if process.returncode:
      print(stderrdata)
      print("problem running command : \n   ", str(command), " ",process.returncode)

    return stdoutdata

"""run command with no output piping"""
def run_command(command,cwd=None, shell=True):
    import subprocess
    process = None
    try:
        process = subprocess.Popen(command, shell=shell, cwd=cwd)
        print(str(process))
    except Exception as inst:
        print("1. problem running command : \n   ", str(command), "\n problem : ", str(inst))

    process.communicate()  # wait for the process to end

    if process.returncode:
        print("2. problem running command : \n   ", str(command), " ", process.returncode)
        


        
class TestbTCPFramework(unittest.TestCase):
    """Test cases for bTCP"""
    
    def setUp(self):
        """Prepare for testing"""
        # default netem rule (does nothing)
        run_command(netem_add)
        
        # launch localhost server
        self.server = BTCPServerSocket(timeout, winsize)

        # generate some random data to send
        self.data = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(50000))
        self.expectednumofsegments = math.ceil(len(self.data) / 1008)

        print("Server started!")
        

    def tearDown(self):
        """Clean up after testing"""
        # clean the environment
        run_command(netem_del)
        
        # close server
        self.server.close()


    def test_ideal_network(self):
        """reliability over an ideal framework"""
        # setup environment (nothing to set)

        # launch localhost client connecting to server
        socket = BTCPClientSocket(winsize, timeout)
        socket.connect()
        print("Connected")
        
        # client sends content to server
        socket.send(self.data.encode())

        # server receives content from client
        recv_data = []
        while len(recv_data) < self.expectednumofsegments:
            r_data = self.server.recv()
            if len(r_data) > 0:
                recv_data.extend(r_data)

        socket.disconnect()

        recv_data = self.assembleData(recv_data)
        r_data = ""
        for t in recv_data:
            r_data += t[0]

        # content received by server matches the content sent by client
        print(str(len(self.data)) + self.data)
        print(str(len(r_data)) + r_data)
        self.assertEqual(self.data, r_data)
    
    def test_flipping_network(self):
        """reliability over network with bit flips 
        (which sometimes results in lower layer packet loss)"""
        # setup environment
        run_command(netem_change.format("corrupt 1%"))

        # launch localhost client connecting to server
        socket = BTCPClientSocket(winsize, timeout)
        socket.connect()
        print("Connected")

        # client sends content to server
        socket.send(self.data.encode())

        # server receives content from client
        recv_data = []
        while len(recv_data) < self.expectednumofsegments:
            r_data = self.server.recv()
            if len(r_data) > 0:
                recv_data.extend(r_data)

        socket.disconnect()

        recv_data = self.assembleData(recv_data)
        r_data = ""
        for t in recv_data:
            r_data += t[0]

        # content received by server matches the content sent by client
        print(self.data)
        print(r_data)
        self.assertEqual(self.data, r_data)

    def test_duplicates_network(self):
        """reliability over network with duplicate packets"""
        # setup environment
        run_command(netem_change.format("duplicate 10%"))

        socket = BTCPClientSocket(10, 10)
        socket.connect()
        print("Connected")

        # client sends content to server
        socket.send(self.data.encode())

        # server receives content from client
        recv_data = []
        while len(recv_data) < self.expectednumofsegments:
            r_data = self.server.recv()
            if len(r_data) > 0:
                recv_data.extend(r_data)

        socket.disconnect()

        recv_data = self.assembleData(recv_data)
        r_data = ""
        for t in recv_data:
            r_data += t[0]

        # content received by server matches the content sent by client
        print(self.data)
        print(r_data)
        self.assertEqual(self.data, r_data)

    def test_lossy_network(self):
        """reliability over network with packet loss"""
        # setup environment
        run_command(netem_change.format("loss 10% 25%"))

        socket = BTCPClientSocket(10, 10)
        socket.connect()
        print("Connected")

        # client sends content to server
        socket.send(self.data.encode())

        # server receives content from client
        recv_data = []
        while len(recv_data) < self.expectednumofsegments:
            r_data = self.server.recv()
            if len(r_data) > 0:
                recv_data.extend(r_data)

        socket.disconnect()

        recv_data = self.assembleData(recv_data)
        r_data = ""
        for t in recv_data:
            r_data += t[0]

        # content received by server matches the content sent by client
        print(self.data)
        print(r_data)
        self.assertEqual(self.data, r_data)

    def test_reordering_network(self):
        """reliability over network with packet reordering"""
        # setup environment
        run_command(netem_change.format("delay 20ms reorder 25% 50%"))

        socket = BTCPClientSocket(winsize, timeout)
        socket.connect()
        print("Connected")

        # client sends content to server
        socket.send(self.data.encode())

        # server receives content from client
        recv_data = []
        while len(recv_data) < self.expectednumofsegments:
            r_data = self.server.recv()
            if len(r_data) > 0:
                recv_data.extend(r_data)

        socket.disconnect()

        recv_data = self.assembleData(recv_data)
        r_data = ""
        for t in recv_data:
            r_data += t[0]

        # content received by server matches the content sent by client
        print(self.data)
        print(r_data)
        self.assertEqual(self.data, r_data)
        
    def test_delayed_network(self):
        """reliability over network with delay relative to the timeout value"""
        # setup environment
        run_command(netem_change.format("delay "+str(timeout)+"ms 20ms"))

        socket = BTCPClientSocket(10, 1)
        socket.connect()
        print("Connected")

        # client sends content to server
        socket.send(self.data.encode())

        # server receives content from client
        recv_data = []
        while len(recv_data) < self.expectednumofsegments:
            r_data = self.server.recv()
            if len(r_data) > 0:
                recv_data.extend(r_data)

        socket.disconnect()

        recv_data = self.assembleData(recv_data)
        r_data = ""
        for t in recv_data:
            r_data += t[0]

        # content received by server matches the content sent by client
        print(self.data)
        print(r_data)
        self.assertEqual(self.data, r_data)
    
    def test_allbad_network(self):
        """reliability over network with all of the above problems"""

        # setup environment
        run_command(netem_change.format("corrupt 1% duplicate 10% loss 10% 25% delay 20ms reorder 25% 50%"))

        socket = BTCPClientSocket(10, 10)
        socket.connect()
        print("Connected")

        # client sends content to server
        socket.send(self.data.encode())

        # server receives content from client
        recv_data = []
        while len(recv_data) < self.expectednumofsegments:
            r_data = self.server.recv()
            if len(r_data) > 0:
                recv_data.extend(r_data)

        socket.disconnect()

        recv_data = self.assembleData(recv_data)
        r_data = ""
        for t in recv_data:
            r_data += t[0]

        # content received by server matches the content sent by client
        print(self.data)
        print(r_data)
        self.assertEqual(self.data, r_data)

    def assembleData(self, data):
        # we have a list of tuples, sort it by their second element
        data.sort(key=lambda x: x[1])
        return data

  
#    def test_command(self):
#        #command=['dir','.']
#        out = run_command_with_output("dir .")
#        print(out)
        

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="bTCP tests")
    parser.add_argument("-w", "--window", help="Define bTCP window size used", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define the timeout value used (ms)", type=int, default=1)
    parser.add_argument("-p", "--password", help="Give user password", type=string, default=password)
    args, extra = parser.parse_known_args()
    timeout = args.timeout
    winsize = args.window
    password = args.password
    
    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main()