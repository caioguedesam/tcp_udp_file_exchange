import socket
import threading, os
from message_utils import *

class Server:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind((self.addr, self.port))

        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind((self.addr, self.port))

        self.header_size = 2

    def listen(self):
        self.tcp_sock.listen()
        while True:
            c_sock, c_addr = self.tcp_sock.accept()
            c_sock.settimeout(60)
            threading.Thread(target = self.client_thread, args = (c_sock, c_addr)).start()

    def client_thread(self, c_sock, c_addr):
        try:
            buf_size = 1024
            
            #udp_data, udp_addr = self.udp_sock.recvfrom(buf_size)
            #print('Received udp data: ' + udp_data.decode() + ', from ' + str(udp_addr))
            # TODO: Server needs to bind a new udp port for each client when connecting (?).

            while True:
                data = c_sock.recv(buf_size)
                # Close client socket if no data incoming from client
                if not data or len(data) == 0:
                    break
                print(data.decode() + ' | size: ' + str(len(data)))
                response = data
                c_sock.send(response)
            print('Closing socket') 
            c_sock.close()
        # Close client socket if client times out
        except socket.timeout:
            print('Timeout')
            c_sock.close()

if __name__ == "__main__":
    ip = '127.0.0.1'
    port = 5151

    try:
        server = Server(ip, port)
        server.listen()
    except KeyboardInterrupt:
        os._exit(1)