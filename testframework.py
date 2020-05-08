import unittest
import socket
import time
import sys
from btcp.server_socket import BTCPServerSocket
from btcp.client_socket import BTCPClientSocket
import string
import random

timeout=100
winsize=100
intf="lo"
netem_add="sudo tc qdisc add dev {} root netem".format(intf)
netem_change="sudo tc qdisc change dev {} root netem {}".format(intf,"{}")
netem_del="sudo tc qdisc del dev {} root netem".format(intf)

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
    """function for testing"""
    def createClient(self):
        # launch localhost client connecting to server
        socket = BTCPClientSocket(timeout, winsize)
        socket.connect()
        while not socket.getStatus() == 3:
            pass
    
    def sendMessage(self):
        # client sends content to server
        # generate 100 bytes of random data
        data = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(100))
        socket.send(data.encode())
        return data
    
    def getMessage(self):
        while self.server.isActive():
            r_data = self.server.recv()
            if len(r_data) > 0:
                socket.disconnect()
                return r_data[0]

    """Test cases for bTCP"""
    
    def setUp(self):
        """Prepare for testing"""
        # default netem rule (does nothing)
        run_command(netem_add)
        
        # launch localhost server
        self.server = BTCPServerSocket(timeout, winsize)
        

    def tearDown(self):
        """Clean up after testing"""
        # clean the environment
        run_command(netem_del)
        
        # close server
        self.server.close()

    def test_ideal_network(self):
        """reliability over an ideal framework"""
        # setup environment
        setUp()

        # launch localhost client connecting to server
        createClient()

        # client sends content to server
        data = sendMessage()

        # server receives content from client
        recv_data = getMessage()

        # content received by server matches the content sent by client
        self.assertEqual(data, recv_data)
    
    def test_flipping_network(self):
        """reliability over network with bit flips 
        (which sometimes results in lower layer packet loss)"""
        # setup environment
        run_command(netem_change.format("corrupt 1%"))
        setUp()

        # launch localhost client connecting to server
        createClient()

        # client sends content to server
        data = sendMessage()

        # server receives content from client
        recv_data = getMessage()

        # content received by server matches the content sent by client
        self.assertEqual(data, recv_data)

    def test_duplicates_network(self):
        """reliability over network with duplicate packets"""
        # setup environment
        run_command(netem_change.format("duplicate 10%"))
        setUp()

        # launch localhost client connecting to server
        createClient()

        # client sends content to server
        data = sendMessage()

        # server receives content from client
        recv_data = getMessage()

        # content received by server matches the content sent by client
        self.assertEqual(data, recv_data)

    def test_lossy_network(self):
        """reliability over network with packet loss"""
        # setup environment
        run_command(netem_change.format("loss 10% 25%"))
        setUp()

        # launch localhost client connecting to server
        createClient()

        # client sends content to server
        data = sendMessage()

        # server receives content from client
        recv_data = getMessage()

        # content received by server matches the content sent by client
        self.assertEqual(data, recv_data)

    def test_reordering_network(self):
        """reliability over network with packet reordering"""
        # setup environment
        run_command(netem_change.format("delay 20ms reorder 25% 50%"))
        setUp()

        # launch localhost client connecting to server
        createClient()

        # client sends content to server
        data = sendMessage()

        # server receives content from client
        recv_data = getMessage()

        # content received by server matches the content sent by client
        self.assertEqual(data, recv_data)
        
    def test_delayed_network(self):
        """reliability over network with delay relative to the timeout value"""
        # setup environment
        run_command(netem_change.format("delay "+str(timeout)+"ms 20ms"))
        setUp()

        # launch localhost client connecting to server
        createClient()

        # client sends content to server
        data = sendMessage()

        # server receives content from client
        recv_data = getMessage()

        # content received by server matches the content sent by client
        self.assertEqual(data, recv_data)
    
    def test_allbad_network(self):
        """reliability over network with all of the above problems"""

        # setup environment
        run_command(netem_change.format("corrupt 1% duplicate 10% loss 10% 25% delay 20ms reorder 25% 50%"))
        setUp()

        # launch localhost client connecting to server
        createClient()

        # client sends content to server
        data = sendMessage()

        # server receives content from client
        recv_data = getMessage()

        # content received by server matches the content sent by client
        self.assertEqual(data, recv_data)

  
#    def test_command(self):
#        #command=['dir','.']
#        out = run_command_with_output("dir .")
#        print(out)
        

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="bTCP tests")
    parser.add_argument("-w", "--window", help="Define bTCP window size used", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define the timeout value used (ms)", type=int, default=timeout)
    args, extra = parser.parse_known_args()
    timeout = args.timeout
    winsize = args.window
    
    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main()
    sys.exit(0)
