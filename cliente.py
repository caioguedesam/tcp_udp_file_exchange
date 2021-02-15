import socket
import threading
import sys, os
from message_utils import *
from sliding_window import SlidingWindow

class Client:
    def __init__(self, s_addr, s_port, file_name):
        self.s_addr = s_addr
        self.s_port = s_port
        self.file_name = file_name

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((s_addr, s_port))

    def init_conn(self):
        # Sending HELLO message to identify
        print('Sending HELLO to server...')
        hello = make_header(message_type.HELLO, message_channel.CONTROL)
        self.tcp_sock.send(hello)

        # Receiving CONNECTION message with UDP port data
        data = self.tcp_sock.recv(CONN_len)
        if parse_header(data) != (message_type.CONNECTION, message_channel.CONTROL):
            print('ERROR: didn\'t receive CONNECTION from server.')
            self.close()

        # Making UDP socket to send file with
        port = data[HEADER_len:]
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_port = int.from_bytes(port, byteorder='big')
        print('Received CONNECTION from server, with port: ' + str(self.udp_port))

    def send_file_data(self):
        # Only send INFO message if file exists
        if not os.path.isfile(self.file_name):
            print('File not found on current path.')
            return
        
        # Sending INFO message with file name and size
        size = os.stat(self.file_name).st_size
        info = info_msg(self.file_name, size)
        print('Sending INFO message to server. File name: ' + str(self.file_name) + ', size: ' + str(size))
        self.tcp_sock.send(info)

        # Receiving OK from server
        data = self.tcp_sock.recv(OK_len)
        if parse_header(data) != (message_type.OK, message_channel.CONTROL):
            print('ERROR: didn\'t receive OK from server.')
            self.close()
        print('Received OK from server.')

    def close(self):
        print('Closing client')
        self.tcp_sock.close()
        os._exit(1)

if __name__ == "__main__":
    if(len(sys.argv)) != 4:
        print('Usage: python3 cliente.py <server_ip> <server_port> <file_name>')
        print('Example: python3 cliente.py 127.0.0.1 51511 file.txt')
    else:
        client = Client(sys.argv[1], int(sys.argv[2]), sys.argv[3])
        client.init_conn()
        client.send_file_data()
        client.close()
