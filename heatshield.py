#!/usr/bin/env python3.6
"""
heatshield.py

Practice coding a simple commandline TCP proxy. Started with the Black Hat Python example and updated and expanded
code from Python 2 into Python 3. May expand upon this periodically.

"""

__author__ = "Felajan"
__copyright__ = "Copyright 2018, Felajan"
__credits__ = ["Felajan",]
__version__ = "1.0.0"
__maintainer__ = "Felajan"
__email__ = "felajan@protonmail.com"
__status__ = "Development"
__created_date__ = "2018-03-13"
__modified_date__ = "2018-03-20"

import sys
import socket
import threading
import hexdump
import argparse


class HeatShield():
    def __init__(self):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("localhost")
        parser.add_argument("localport", type=int)
        parser.add_argument("remotehost")
        parser.add_argument("remoteport", type=int)
        parser.add_argument("receive_first")

        self.args = parser.parse_args()

        self.verify_args()

        if self.args.receive_first.casefold() == "true" or self.args.receive_first.casefold() == "t":
            self.args.receive_first = True
        else:
            self.args.receive_first = False

        self.server_loop()

    def server_loop(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.bind((self.args.localhost, self.args.localport))
        except:
            print("[***] Failed to listen on {}:{}".format(self.args.localhost, self.args.localport))
            print("[***] Check for other listening sockets or correct permissions.")
            sys.exit(0)

        print("[*] Listening on {}:{}".format(self.args.localhost, self.args.localport))

        server.listen(5)

        while True:
            client_socket, addr = server.accept()

            # print out the local connection information
            print("[==>] Received incoming connection from {}:{}".format(addr[0], addr[1]))

            # start a thread to talk to the remote host
            proxy_thread = threading.Thread(target=self.proxy_handler, args=(client_socket, self.args.remotehost,
                                                                         self.args.remoteport, self.args.receive_first))
            proxy_thread.start()

    def proxy_handler(self, client_socket, remote_host, remote_port, receive_first):
        # connect to the remote host
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((remote_host, remote_port))

        # receive data from remote end if necessary
        if receive_first:
            remote_buffer = self.receive_from(remote_socket)
            hexdump.hexdump(remote_buffer)

            # send it to our response handler
            remote_buffer = self.response_handler(remote_buffer)

            # if we have data to send to our local client, send it
            if len(remote_buffer):
                print("[<==] Sending {} bytes to localhost.".format(len(remote_buffer)))

        # now loop and read from local
        # send to remote, send to local
        # repeat

        while True:
            # read from local host
            local_buffer = self.receive_from(client_socket)

            if len(local_buffer):
                print("[==>] Received {} bytes from localhost.".format(len(local_buffer)))
                hexdump.hexdump(local_buffer)

            # send it to our request handler
            local_buffer = self.request_handler(local_buffer)

            # send the data off to our remote host
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

            # receive back the response
            remote_buffer = self.receive_from(remote_socket)

            if len(remote_buffer):
                print("[<==] Received {} bytes from remote host.".format(len(remote_buffer)))
                hexdump.hexdump(remote_buffer)

                # send to our response handler
                remote_buffer = self.response_handler(remote_buffer)

                # send the response to our local socket
                client_socket.send(remote_buffer)

                print("[<==] Sent to localhost.")

            # if no more data on either side, close the connections
            if not len(local_buffer) or not len(remote_buffer):
                client_socket.close()
                remote_socket.close()
                print("[***] No more data. Closing connection.")
                break

    def receive_from(self, connection):
        buffer = ""
        # we set 2 second timeout
        # depending on your target, may need to adjust
        connection.settimeout(2)

        try:
            # keep reading into the buffer until there is no more data
            # or we time out
            while True:
                data = connection.recv(4096)

                if not data:
                    break

                buffer += data
        except:
            pass

        return buffer

    def request_handler(self, buffer):
        # perform packet modifications
        buffer = bytes(buffer, 'utf8')
        return buffer

    def response_handler(self, buffer):
        # perform packet modifications
        buffer = bytes(buffer, 'utf8')
        return buffer


if __name__ == "__main__":
    HeatShield()
