#!/usr/local/bin/python3

import argparse
from btcp.client_socket import BTCPClientSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=2000)
    parser.add_argument("-i", "--input", help="File to send", default="input.file")
    args = parser.parse_args()

    # Create a bTCP client socket with the given window size and timeout value
    s = BTCPClientSocket(args.window, args.timeout/1000)
    s.connect()
    print("Connected!")

    f = None

    try:
        f = open(args.input)
        lines = f.read().encode()
        print("Sending file...")
        sendFile(lines, s, 0)
    except IOError:
        print("File does not exist!")
    finally:
        print("Closing connection...")
        while (len(s.sbuffer) > 0):
            pass
        s.disconnect()
        print("File sent!")

    return 0

def sendFile(filedata, socket, sent):
    try:
        socket.send(filedata)
    except ValueError as e:
        size = int(e.args[0])
        slice = filedata[sent:size]
        sendFile(slice, socket, 0)
        if (len(filedata) - sent) > 0:
            sendFile(filedata, socket, size)


main()
quit()