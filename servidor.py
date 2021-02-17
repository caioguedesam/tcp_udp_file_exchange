import socket
import threading
import sys, os
from timer import Timer
from message_utils import *

class Server:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind((self.addr, self.port))

        self.window_size = 4

    def listen(self):
        self.tcp_sock.listen()
        while True:
            c_sock, c_addr = self.tcp_sock.accept()
            threading.Thread(target = self.client_thread, args = (c_sock, c_addr)).start()

    def init_conn(self, c_sock, c_addr):
        # Receiving HELLO message from client
        data = c_sock.recv(HELLO_len)
        if parse_header(data) != (message_type.HELLO, message_channel.CONTROL):
            print('Error: didn\'t receive HELLO from client at ' + str(c_addr[0]) + ':' + str(c_addr[1]))
            return 0, 0
        print('Received HELLO from client ' + str(c_addr[0]) + ':' + str(c_addr[1]))

        # Creating new UDP socket for receiving client data
        c_data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        c_data_sock.bind((self.addr, 0))

        # Confirming CONNECTION and sending appropriate port
        c_data_port = c_data_sock.getsockname()[1]
        connection = connection_msg(c_data_port)
        c_sock.send(connection)
        print('Sent CONNECTION message to client ' + str(c_addr[0]) + ':' + str(c_addr[1]) + ', with UDP port: ' + str(c_data_port))
        return c_data_sock, c_data_port

    def get_file_info(self, c_sock):
        # Receiving INFO message from client with file information
        data = c_sock.recv(INFO_len)
        if parse_header(data) != (message_type.INFO, message_channel.CONTROL):
            print('Error: didn\'t receive INFO from client')
            return 0, 0
        
        file_info = data[HEADER_len:]
        file_name = file_info[:INFO_filename_len].decode(encoding="ascii").lstrip('\x00')
        file_size = int.from_bytes(file_info[INFO_filename_len:], byteorder='big')
        print('Received INFO from client ' + repr(file_name) + ':' + str(file_size))

        # Sending OK message to client
        ok = ok_msg()
        c_sock.send(ok)
        print('Sent OK')
        return file_name, file_size


    def client_thread(self, c_sock, c_addr):
        c_data_sock, c_data_port = self.init_conn(c_sock, c_addr)

        if (c_data_sock, c_data_port) == (0, 0):
            print('ERROR: Closing socket') 
            c_sock.close()
            return

        file_name, file_size = self.get_file_info(c_sock)
        if (file_name, file_size) == (0, 0):
            print('ERROR: Closing socket')
            c_sock.close()
            return

        # Receive file
        pkt_expected = 0
        #f = open(os.path.join('output', file_name), 'wb')
        with open(os.path.join('output', file_name), 'wb') as f:
            while True:
                # Receive data
                data, addr = c_data_sock.recvfrom(FILE_max_len)
                # Stop loop when no data is sent anymore.
                if not data:
                    break
                header = data[:HEADER_len]
                if parse_header(header) != (message_type.FILE, message_channel.DATA):
                    print('Error: received message on UDP that was not FILE message.')
                    continue
                
                seq_num = int.from_bytes(data[HEADER_len:HEADER_len + FILE_seq_num_len], byteorder='big')
                print('Received packet with seq num: ' + str(seq_num))

                if seq_num == pkt_expected:
                    # Got expected packet, writing to file
                    print('Got expected packet (' + str(seq_num) + ')')
                    print('Sending ACK for ' + str(pkt_expected))
                    c_sock.send(ack_msg(pkt_expected))
                    # Expect next packet
                    pkt_expected += 1
                    # Write to file after sending ack
                    pkt_data = data[HEADER_len + FILE_seq_num_len + FILE_payload_size_len:]
                    print('Writing ' + pkt_data.decode())
                    print('Status: ' + str(f.write(pkt_data) > 0))
                else:
                    # Didn't get expected packet, resend ack for last acknowledged packet
                    print('Sending ACK for ' + str(pkt_expected - 1))
                    c_sock.send(ack_msg(pkt_expected - 1))

        #f.close()
        # Close client thread after finishing file transfer
        print('Closing socket') 
        c_sock.close()

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print('Usage: python3 servidor.py <server_port>')
            print('Example: python3 servidor.py 51511')
        else:
            ip = '127.0.0.1'
            server = Server(ip, int(sys.argv[1]))
            server.listen()
    except KeyboardInterrupt:
        os._exit(1)