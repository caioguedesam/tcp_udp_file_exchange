from enum import Enum

# Sizes of data elements from each message type, in bytes
HEADER_len = 2
CONN_port_len = 4
INFO_filename_len = 15
INFO_file_len = 8
FILE_seq_num_len = 4
FILE_payload_size_len = 2
FILE_payload_max_len = 1000
ACK_seq_num_len = FILE_seq_num_len

# Sizes of each TCP message type, in bytes
HELLO_len, OK_len, END_len = HEADER_len, HEADER_len, HEADER_len
CONN_len = HEADER_len + CONN_port_len
INFO_len = HEADER_len + INFO_filename_len + INFO_file_len
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

def parse_header(header):
    header_values = list(header)
    # Convert values from header into correct enum types
    header_type = message_type(header_values[0])
    header_channel = message_channel(header_values[1])
    return (header_type, header_channel)

# Makes HELLO message from client
def hello_msg():
    return make_header(message_type.HELLO, message_channel.CONTROL)

# Makes CONNECTION message from server, with UDP port for client to send data to
def connection_msg(udp_port):
    header = make_header(message_type.CONNECTION, message_channel.CONTROL)
    port = udp_port.to_bytes(CONN_port_len, byteorder='big')
    msg = header + port
    return msg

# Returns if a given file name is valid or not, when sending INFO message
def valid_file_name(file_name):
    try:
        # File name needs to be a valid ASCII string
        file_name_ascii = file_name.encode(encoding="ascii")

        # File name size needs to be 15 bytes at most
        if len(file_name.encode()) > INFO_filename_len:
            return False
        
        # File name needs to have only one dot
        dot_count = file_name.count('.')
        if dot_count != 1:
            return False
        
        # File name needs to have at least 3 characters after dot
        file_name_split = file_name.split('.')
        if len(file_name_split[1]) < 3:
            return False
        
        return True
    except UnicodeError:
        return False

# Makes INFO message from client, with file name and size for uploading.
def info_msg(file_name, file_size):
    if(not valid_file_name(file_name)):
        print('Nome não permitido')
        return ''
    header = make_header(message_type.INFO, message_channel.CONTROL)
    # Name always with 15 bytes
    name = file_name.encode(encoding="ascii")
    name = b'\x00' * (INFO_filename_len - len(name)) + name
    size = file_size.to_bytes(INFO_file_len, byteorder='big')
    msg = header + name + size
    return msg

# Makes OK message from server, after allocating structures to receive file w/ udp.
def ok_msg():
    return make_header(message_type.OK, message_channel.CONTROL)

# Makes END message from server, when server received all packets.
def end_msg():
    return make_header(message_type.END, message_channel.CONTROL)

# Makes list of FILE messages, from file to upload to server. Each message contains a
# sequence number to identify its order in the file, as well as message size and data.
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

# Makes ACK message from server, confirming receiving FILE message with
# specified sequence number.
def ack_msg(seq_num):
    header = make_header(message_type.ACK, message_channel.CONTROL)
    msg = header + seq_num.to_bytes(ACK_seq_num_len, byteorder='big')
    return msg