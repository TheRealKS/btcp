#!/usr/local/bin/python3

import argparse
from btcp.client_socket import BTCPClientSocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
    parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
    parser.add_argument("-i", "--input", help="File to send", default="input.file")
    args = parser.parse_args()

    # Create a bTCP client socket with the given window size and timeout value
    s = BTCPClientSocket(args.window, args.timeout)
    s.connect()
    print("Connected!")

    try:
        f = open(args.input)
        lines = f.read().encode()
        sendFile(lines, s, 0)
    except IOError:
        print("File does not exist!")
    finally:
        f.close()

    # Clean up any state
    s.disconnect()


def sendFile(filedata, socket, sent):
    try:
        socket.send(filedata)
    except ValueError as e:
        size = e.args[0]
        slice = filedata[sent, size]
        sendFile(slice, socket, 0)
        if len(filedata) > 0:
            sendFile(filedata, socket, size)


main()
