import socket
import threading
import sys, os, time
from message_utils import *

WINDOW_SIZE = 4
TIMEOUT_TIME = 5
SLEEP_TIME = 0.25

window_mutex = threading.Lock()

class Client:
    def __init__(self, s_addr, s_port, file_name):
        self.s_addr = s_addr
        self.s_port = s_port
        self.file_name = file_name

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((s_addr, s_port))

        self.next_packet_to_send = 0
        # ACKed packets until last_acked (not including it).
        self.last_acked = 0
        self.end_conn = False

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
        self.file_pkt_count = msg_count(size)
        info = info_msg(self.file_name, size)
        print('Sending INFO message to server. File name: ' + str(self.file_name) + ', size: ' + str(size))
        self.tcp_sock.send(info)

        # Receiving OK from server
        data = self.tcp_sock.recv(OK_len)
        if parse_header(data) != (message_type.OK, message_channel.CONTROL):
            print('ERROR: didn\'t receive OK from server.')
            self.close()
        print('Received OK from server.')

    def send_file(self):
        global window_mutex
        global timer
        packets = file_msg(self.file_name)
        packet_count = len(packets)
        print('Sending file, packet count: ' + str(packet_count))
        
        threading.Thread(target=self.receive_ack).start()

        while self.last_acked < packet_count:
            print('ENTERING LOOP, LAST ACKED: ' + str(self.last_acked) + ', PKT COUNT: ' + str(packet_count))
            window_mutex.acquire()
            if self.next_packet_to_send >= packet_count:
                continue

            while self.next_packet_to_send < self.last_acked + WINDOW_SIZE and self.next_packet_to_send < packet_count:
                print('Sending packet ' + str(self.next_packet_to_send) + '...')
                self.udp_sock.sendto(packets[self.next_packet_to_send], (self.s_addr, self.udp_port))
                self.next_packet_to_send += 1
            
            start_time = time.time()
            while self.last_acked != self.next_packet_to_send and time.time() < start_time + TIMEOUT_TIME:
                print('Waiting... last ACKed: ' + str(self.last_acked) + ', next to send: ' + str(self.next_packet_to_send))
                window_mutex.release()
                time.sleep(SLEEP_TIME)
                window_mutex.acquire()

            # Timeout
            if self.last_acked != self.next_packet_to_send:
                self.next_packet_to_send = self.last_acked
            window_mutex.release()

        print('Finished sending')
        self.close()

    def receive_ack(self):
        global window_mutex
        global timer

        while True:
            data = self.tcp_sock.recv(ACK_len)
            if not data:
                break
            if parse_header(data) == (message_type.END, message_channel.CONTROL):
                print('Received END from server. Shutting down connection')
                break
            elif parse_header(data) != (message_type.ACK, message_channel.CONTROL):
                print('Error: got message of type different than ACK or END.')
            else:
                ack = int.from_bytes(data[HEADER_len:], byteorder='big')
                if ack > self.last_acked:
                    self.last_acked = ack
                print('Received ACK ' + str(ack) + ', last ACKed: ' + str(self.last_acked))
                if ack >= self.next_packet_to_send:
                    window_mutex.acquire()
                    self.next_packet_to_send = ack
                    print('Next to send: ' + str(self.next_packet_to_send))
                    timer.stop()
                    window_mutex.release()
        print('Received all packets.')      

    def close(self):
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
        client.send_file()
