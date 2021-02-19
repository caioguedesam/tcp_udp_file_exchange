import socket, threading
import sys, time
from os.path import isfile
from os import stat
from message_utils import *

WINDOW_SIZE = 4
TIMEOUT_TIME = 5
SLEEP_TIME = 0.01

window_mutex = threading.Lock()

class Client:
    def __init__(self, s_addr, s_port, file_name):
        self.s_addr = s_addr
        self.s_port = s_port
        self.file_name = file_name

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((s_addr, s_port))

        self.next_packet_to_send = 0
        self.last_acked = 0

    # Inicia conexão com servidor. Engloba mensagens HELLO e CONNECTION.
    def init_conn(self):
        # Mandando mensagem HELLO
        hello = make_header(message_type.HELLO, message_channel.CONTROL)
        self.tcp_sock.send(hello)

        # Recebendo mensagem CONNECTION com porta UDP
        data = self.tcp_sock.recv(CONN_len)
        if parse_header(data) != (message_type.CONNECTION, message_channel.CONTROL):
            print('ERRO: Não recebeu mensagem do tipo CONNECTION do servidor.')
            self.close()

        # Alocando socket UDP para enviar arquivo
        port = data[HEADER_len:]
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_port = int.from_bytes(port, byteorder='big')

    # Envia dados gerais do arquivo para o servidor. Engloba mensagens INFO e OK.
    def send_file_data(self):
        if not isfile(self.file_name):
            print('ERRO: Arquivo não encontrado na pasta atual.')
            return
        
        # Mandando mensagem INFO com nome e tamanho do arquivo
        size = stat(self.file_name).st_size
        self.file_pkt_count = msg_count(size)
        info = info_msg(self.file_name, size)
        self.tcp_sock.send(info)

        # Recebendo mensagem OK
        data = self.tcp_sock.recv(OK_len)
        if parse_header(data) != (message_type.OK, message_channel.CONTROL):
            print('ERRO: Não recebeu mensagem do tipo OK do servidor.')
            self.close()

    # Envia o arquivo para o servidor. Engloba mensagens FILE.
    def send_file(self):
        global window_mutex
        packets = file_msg(self.file_name)
        packet_count = len(packets)
        
        # Criando thread separada para receber mensagens ACK do servidor
        recv_th = threading.Thread(target=self.receive_ack)
        recv_th.start()

        # Enviando arquivo até receber confirmação de todos os pacotes.
        while self.last_acked < packet_count:
            window_mutex.acquire()
            if self.next_packet_to_send >= packet_count:
                continue

            # Envia próximo pacote até o limite da janela ou até o último pacote
            while self.next_packet_to_send < self.last_acked + WINDOW_SIZE and self.next_packet_to_send < packet_count:
                self.udp_sock.sendto(packets[self.next_packet_to_send], (self.s_addr, self.udp_port))
                self.next_packet_to_send += 1
            
            # Começa tempo de espera
            start_time = time.time()
            while self.last_acked != self.next_packet_to_send and time.time() < start_time + TIMEOUT_TIME:
                window_mutex.release()
                time.sleep(SLEEP_TIME)
                window_mutex.acquire()

            # Timeout caso último pacote confirmado não seja o antecessor do próximo a ser enviado.
            if self.last_acked != self.next_packet_to_send:
                print('ERRO: Timeout ocorrido. Reenviando pacotes na janela.')
                self.next_packet_to_send = self.last_acked
            window_mutex.release()
        
        recv_th.join()

    # Recebe mensagens do servidor após começar a enviar o arquivo. Engloba mensagens ACK e FIM.
    def receive_ack(self):
        global window_mutex

        while True:
            data = self.tcp_sock.recv(ACK_len)
            if not data:
                break
            # Caso receba FIM, termina a recepção de mensagens
            if parse_header(data) == (message_type.END, message_channel.CONTROL):
                print('Arquivo enviado com sucesso.')
                break
            elif parse_header(data) != (message_type.ACK, message_channel.CONTROL):
                print('ERRO: Recebeu mensagem de outro tipo que não ACK ou FIM.')
            # Recebeu ACK do servidor
            else:
                ack = int.from_bytes(data[HEADER_len:], byteorder='big')
                # Atualiza o último pacote confirmado
                if ack > self.last_acked:
                    self.last_acked = ack
                # Atualiza o próximo pacote a enviar
                if ack >= self.next_packet_to_send:
                    window_mutex.acquire()
                    self.next_packet_to_send = ack
                    window_mutex.release()

if __name__ == "__main__":
    if(len(sys.argv)) != 4:
        print('Usage: python3 cliente.py <server_ip> <server_port> <file_name>')
        print('Example: python3 cliente.py 127.0.0.1 51511 file.txt')
    else:
        client = Client(sys.argv[1], int(sys.argv[2]), sys.argv[3])
        client.init_conn()
        client.send_file_data()
        client.send_file()
        client.tcp_sock.close()
