from enum import Enum

# Tamanho de cada elemento de mensagem, em bytes
HEADER_len = 2
CONN_port_len = 4
INFO_filename_len = 15
INFO_file_len = 8
FILE_seq_num_len = 4
FILE_payload_size_len = 2
FILE_payload_max_len = 1000
ACK_seq_num_len = FILE_seq_num_len

# Tamanho de cada tipo de mensagem, em bytes
HELLO_len, OK_len, END_len = HEADER_len, HEADER_len, HEADER_len
CONN_len = HEADER_len + CONN_port_len
INFO_len = HEADER_len + INFO_filename_len + INFO_file_len
FILE_max_len = HEADER_len + FILE_seq_num_len + FILE_payload_size_len + FILE_payload_max_len
ACK_len = HEADER_len + ACK_seq_num_len

class message_type(Enum):
    HELLO = 1
    CONNECTION = 2
    INFO = 3
    OK = 4
    END = 5
    FILE = 6
    ACK = 7

class message_channel(Enum):
    CONTROL = 1
    DATA = 2

def make_header(type, channel):
    header_bytes = [type.value.to_bytes(1, byteorder='big'), channel.value.to_bytes(1, byteorder='big')]
    header = header_bytes[0] + header_bytes[1]
    return header

def parse_header(msg):
    header = msg[:HEADER_len]
    header_values = list(header)
    # Convertendo valores do cabeçalho para classificações correspondentes.
    header_type = message_type(header_values[0])
    header_channel = message_channel(header_values[1])
    return (header_type, header_channel)

# Gera mensagem HELLO
def hello_msg():
    return make_header(message_type.HELLO, message_channel.CONTROL)

# Gera mensagem CONNECTION
def connection_msg(udp_port):
    header = make_header(message_type.CONNECTION, message_channel.CONTROL)
    port = udp_port.to_bytes(CONN_port_len, byteorder='big')
    return header + port

# Retorna se o nome de um arquivo é válido ou não, na mensagem INFO
def valid_file_name(file_name):
    try:
        # Nome precisa ser uma string ASCII válida
        file_name_ascii = file_name.encode(encoding="ascii")

        # Nome precisa ter no máximo 15 bytes
        if len(file_name.encode()) > INFO_filename_len:
            return False
        
        # Nome precisa ter apenas um ponto
        dot_count = file_name.count('.')
        if dot_count != 1:
            return False
        
        # Nome precisa ter pelo menos 3 caracteres na extensão
        file_name_split = file_name.split('.')
        if len(file_name_split[1]) < 3:
            return False
        
        return True
    except UnicodeError:
        return False

# Gera mensagem INFO
def info_msg(file_name, file_size):
    if(not valid_file_name(file_name)):
        print('Nome não permitido.')
        return ''
    header = make_header(message_type.INFO, message_channel.CONTROL)
    name = file_name.encode(encoding="ascii")
    # Nome sempre com 15 bytes, com \x00 em bytes vazios na esquerda
    name = b'\x00' * (INFO_filename_len - len(name)) + name
    size = file_size.to_bytes(INFO_file_len, byteorder='big')
    return header + name + size

# Faz mensagem OK
def ok_msg():
    return make_header(message_type.OK, message_channel.CONTROL)

# Faz mensagem FIM
def end_msg():
    return make_header(message_type.END, message_channel.CONTROL)

# Gera lista de mensagens FILE, cada uma com um pacote do arquivo a ser enviado.
def file_msg(file_name, max_payload_size = FILE_payload_max_len):
    header = make_header(message_type.FILE, message_channel.DATA)
    f = open(file_name, 'rb')
    payload = f.read(max_payload_size)
    msgs = []
    payload_num = 0
    while(payload):
        seq_num = payload_num.to_bytes(FILE_seq_num_len, byteorder='big')
        payload_size = len(payload).to_bytes(FILE_payload_size_len, byteorder='big')
        msgs += [header + seq_num + payload_size + payload]
        
        payload = f.read(max_payload_size)
        payload_num += 1
    return msgs

# Retorna número de pacotes/mensagens um arquivo precisará dado seu tamanho em bytes.
def msg_count(file_size):
    count = file_size // FILE_payload_max_len
    if file_size % FILE_payload_max_len > 0:
        count += 1
    return count

# Gera mensagem ACK
def ack_msg(seq_num):
    header = make_header(message_type.ACK, message_channel.CONTROL)
    return header + seq_num.to_bytes(ACK_seq_num_len, byteorder='big')