import socket
import threading
import sys, os

class Client:
    def __init__(self, s_addr, s_port):
        self.s_addr = s_addr
        self.s_port = s_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((s_addr, s_port))
        self.buf_size = 1024
    
    def send_thread(self):
        while True:
            data = input()
            # Close socket if no input to send
            if data == "":
                break
            self.sock.send(data.encode())
        self.close()

    def recv_thread(self):
        while True:
            data = self.sock.recv(self.buf_size)
            # Close socket if no data incoming from server
            if not data:
                break
            print('Response: ' + data.decode() + ' | size: '  + str(len(data)))
        self.close()

    def close(self):
        print('Closing client')
        self.sock.close()
        os._exit(1)

if __name__ == "__main__":
    tcp_ip = '127.0.0.1'
    tcp_port = 5151

    client = Client(tcp_ip, tcp_port)
    t_send = threading.Thread(target = client.send_thread).start()
    t_recv = threading.Thread(target = client.recv_thread).start()
