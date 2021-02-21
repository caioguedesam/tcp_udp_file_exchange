import socket
import threading
import sys, os
from message_utils import *
from ip_parser import is_ipv4, is_ipv6

WINDOW_SIZE = 4

class Server:
    def __init__(self, addr4, addr6, port):
        self.addr4 = addr4
        self.addr6 = addr6
        self.port = port

        self.tcp_sock_4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock_4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock_4.bind((self.addr4, self.port))
        self.tcp_sock_6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.tcp_sock_6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock_6.bind((self.addr6, self.port))

    def listen(self, mode = 4):
        sock = self.tcp_sock_4 if mode == 4 else self.tcp_sock_6
        sock.listen()
        while True:
            c_sock, c_addr = sock.accept()
            threading.Thread(target = self.client_thread, args = (c_sock, c_addr)).start()

    # Inicia conexão com um cliente. Engloba mensagens HELLO e CONNECTION.
    def init_conn(self, c_sock, c_addr):
        # Recebendo HELLO
        data = c_sock.recv(HELLO_len)
        if parse_header(data) != (message_type.HELLO, message_channel.CONTROL):
            print('ERRO: Não recebeu mensagem do tipo HELLO do cliente ' + str(c_addr[0]) + ':' + str(c_addr[1]))
            return 0, 0

        # Criando socket UDP para receber arquivo do cliente
        if is_ipv4(c_addr[0]):
            c_data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            c_data_sock.bind((self.addr4, 0))
        elif is_ipv6(c_addr[0]):
            c_data_sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            c_data_sock.bind((self.addr6, 0))

        # Mandando CONNECTION com porta alocada no socket UDP
        c_data_port = c_data_sock.getsockname()[1]
        c_sock.send(connection_msg(c_data_port))
        return c_data_sock, c_data_port

    # Recebe informação do arquivo que o cliente vai enviar. Engloba mensagens INFO e OK.
    def get_file_info(self, c_sock):
        # Recebendo mensagem INFO com nome e tamanho do arquivo
        data = c_sock.recv(INFO_len)
        if parse_header(data) != (message_type.INFO, message_channel.CONTROL):
            print('ERRO: Não recebeu mensagem do tipo INFO.')
            return 0, 0
        file_info = data[HEADER_len:]
        file_name = file_info[:INFO_filename_len].decode(encoding="ascii").lstrip('\x00')
        file_size = int.from_bytes(file_info[INFO_filename_len:], byteorder='big')

        # Mandando OK
        c_sock.send(ok_msg())
        return file_name, file_size

    # Recebe o arquivo de um cliente e retorna uma lista com os dados de cada pacote. Engloba mensagens FILE e ACK.
    def get_file(self, c_sock, c_data_sock, file_size):
        next_packet_to_recv = 0
        pkt_count = msg_count(file_size)
        stored_pkts = [-1 for i in range(msg_count(file_size))]

        while True:
            data, addr = c_data_sock.recvfrom(FILE_max_len)
            if parse_header(data) != (message_type.FILE, message_channel.DATA):
                print('ERRO: Não recebeu mensagem do tipo FILE no canal UDP.')
                continue

            seq_num = int.from_bytes(data[HEADER_len:HEADER_len + FILE_seq_num_len], byteorder='big')
            # Verificando se pacote recebido está na janela apropriada
            if seq_num >= next_packet_to_recv and seq_num < next_packet_to_recv + WINDOW_SIZE:
                pkt_data = data[HEADER_len + FILE_seq_num_len + FILE_payload_size_len:]
                # Caso pacote recebido não tenha sido armazenado, armazena-o
                if stored_pkts[seq_num] == -1:
                    stored_pkts[seq_num] = pkt_data

                # Atualizando o número do último pacote recebido em sequência.
                if seq_num == next_packet_to_recv:
                    next_packet_to_recv += 1
                    while next_packet_to_recv < len(stored_pkts) and stored_pkts[next_packet_to_recv] != -1:
                        next_packet_to_recv += 1

                # Caso todos os pacotes sejam recebidos, manda o último ACK e para de receber.
                if next_packet_to_recv >= pkt_count:
                    c_sock.send(ack_msg(next_packet_to_recv))
                    break
            
            # Mandando ACK do último pacote recebido em sequência (sempre manda o próximo a receber).
            c_sock.send(ack_msg(next_packet_to_recv))
        return stored_pkts

    # Escreve uma lista de pacotes em um arquivo continuamente.
    def write_file(self, file_name, packets):
        file_data = b''
        for i in packets:
            file_data += i
        if len(file_data) > 0:
            f = open(os.path.join('output', file_name), 'wb')
            f.write(file_data)
            f.close()

    # Termina a conexão com um dado cliente. Engloba mensagem FIM.
    def end_connection(self, c_sock):
        # Manda FIM para o cliente após receber o arquivo inteiro.
        c_sock.send(end_msg())
        data = c_sock.recv(HEADER_len)
        if not data:
            c_sock.close()

    # Função executada para receber arquivos de cada cliente em paralelo.
    def client_thread(self, c_sock, c_addr):
        c_data_sock, c_data_port = self.init_conn(c_sock, c_addr)
        if (c_data_sock, c_data_port) == (0, 0):
            c_sock.close()
            return

        file_name, file_size = self.get_file_info(c_sock)
        if (file_name, file_size) == (0, 0):
            c_sock.close()
            return

        # Recebendo arquivo
        pkts = self.get_file(c_sock, c_data_sock, file_size)

        # Escrevendo no arquivo de saída
        self.write_file(file_name, pkts)
        
        # Terminando conexão com cliente
        self.end_connection(c_sock)

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print('Usage: python3 servidor.py <server_port>')
            print('Example: python3 servidor.py 51511')
        else:
            ipv4 = '127.0.0.1'
            ipv6 = '::'
            server = Server(ipv4, ipv6, int(sys.argv[1]))
            # Ouve por clientes em socket ipv4 e ipv6
            listen_ipv4 = threading.Thread(target=server.listen, args=(4,))
            listen_ipv6 = threading.Thread(target=server.listen, args=(6,))
            listen_ipv4.start()
            listen_ipv6.start()
            listen_ipv4.join()
            listen_ipv6.join()
            
    except KeyboardInterrupt:
        os._exit(1)