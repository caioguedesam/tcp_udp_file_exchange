import socket
import threading
import sys, os
from message_utils import *

class Client:
    def __init__(self, s_addr, s_port):
        self.s_addr = s_addr
        self.s_port = s_port

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((s_addr, s_port))
        
        #self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.header_size = 2
        self.buf_size = 1024

    def start_conn(self):
        print('Starting connection with server...')
        hello_header = make_header(message_type.HELLO, message_channel.CONTROL)
        # Sending HELLO message
        self.tcp_sock.send(hello_header)
        # Receiving CONNECTION message with UDP port data
        self.tcp_sock.recv(self.header_size)


    def send_thread(self):
        #self.udp_sock.sendto('CLIENT MESSAGE'.encode(), (self.s_addr, self.s_port))

        while True:
            data = input()
            # Close socket if no input to send
            if data == "":
                break
            self.tcp_sock.send(data.encode())
        self.close()

    def recv_thread(self):
        while True:
            data = self.tcp_sock.recv(self.buf_size)
            # Close socket if no data incoming from server
            if not data:
                break
            print('Response: ' + data.decode() + ' | size: '  + str(len(data)))
        self.close()

    def close(self):
        print('Closing client')
        self.tcp_sock.close()
        os._exit(1)

if __name__ == "__main__":
    ip = '127.0.0.1'
    port = 5151

    client = Client(ip, port)
    t_send = threading.Thread(target = client.send_thread).start()
    t_recv = threading.Thread(target = client.recv_thread).start()
