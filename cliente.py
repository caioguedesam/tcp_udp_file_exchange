import socket

class Client:
    def __init__(self, s_addr, s_port):
        self.s_addr = s_addr
        self.s_port = s_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((s_addr, s_port))
    
    def get_input(self):
        buf_size = 1024
        while True:
            data = input('Send to server: ')
            # Close socket if no input to send
            if data == "":
                break
            self.sock.send(data.encode())
            response = self.sock.recv(buf_size)
            # Close socket if no response incoming from server
            if not response or len(response) == 0:
                break
            print('Response: ' + response.decode() + ' | size: ' + str(len(response)))
        self.sock.close()

if __name__ == "__main__":
    tcp_ip = '127.0.0.1'
    tcp_port = 5151

    client = Client(tcp_ip, tcp_port)
    client.get_input()
