import socket
import threading
import sys, os, time
from timer import Timer
from message_utils import *

WINDOW_SIZE = 4
TIMEOUT_TIME = 5
SLEEP_TIME = 0.25

window_mutex = threading.Lock()
base = 0
timer = Timer(TIMEOUT_TIME)

def set_window_size(packets_to_send):
    global base
    return min(WINDOW_SIZE, packets_to_send - base)

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
        global base
        global timer

        packets = file_msg(self.file_name)
        packet_count = len(packets)
        window_size = set_window_size(packet_count)
        next_to_send = 0
        base = 0

        # Start receiving ack thread
        threading.Thread(target=self.receive_ack).start()

        while base < packet_count:
            window_mutex.acquire()
            while next_to_send < base + window_size:
                print('Sending packet ' + str(next_to_send) + '...')
                self.udp_sock.sendto(packets[next_to_send], (self.s_addr, self.udp_port))
                next_to_send += 1
            
            if not timer.running():
                print('Starting timer')
                timer.start()

            while timer.running() and not timer.timeout():
                window_mutex.release()
                print('Sleeping...')
                time.sleep(SLEEP_TIME)
                window_mutex.acquire()

            if timer.timeout():
                print('Timed out, sending packets again.')
                timer.stop()
                next_to_send = base
            else:
                print('Shifting window')
                window_size = set_window_size(packet_count)
                print('New window size: ' + str(packet_count) + ' - ' + str(base) + ' = ' + str(window_size))
            window_mutex.release()

        print('Finished sending.')
        self.close()

    def receive_ack(self):
        global window_mutex
        global base
        global timer

        while True:
            data = self.tcp_sock.recv(ACK_len)
            if parse_header(data) != (message_type.ACK, message_channel.CONTROL):
                print('Error: received message of type other than ACK.')
            else:
                ack = int.from_bytes(data[HEADER_len:], byteorder='big')
                if ack >= base:
                    window_mutex.acquire()
                    base = ack + 1
                    print('Received ack ' + str(ack) + ', new base: ' + str(base))
                    # Stop timer because of received ack message
                    timer.stop()
                    window_mutex.release()
            

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
        client.send_file()
        client.close()
