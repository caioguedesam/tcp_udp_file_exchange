import socket
import threading, os

class Server:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.addr, self.port))

    def listen(self):
        self.sock.listen()
        while True:
            c_sock, c_addr = self.sock.accept()
            c_sock.settimeout(30)
            threading.Thread(target = self.client_thread, args = (c_sock, c_addr)).start()

    def client_thread(self, c_sock, c_addr):
        try:
            buf_size = 1024
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
    tcp_ip = '127.0.0.1'
    tcp_port = 5151

    try:
        server = Server(tcp_ip, tcp_port)
        server.listen()
    except KeyboardInterrupt:
        os._exit(1)