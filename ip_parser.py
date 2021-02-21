import socket

def is_ipv4(addr):
    try:
        socket.inet_pton(socket.AF_INET, addr)
    except AttributeError:
        try:
            socket.inet_aton(addr)
        except socket.error:
            return False
        return addr.count('.') == 3
    except socket.error:
        return False

def is_ipv6(addr):
    try:
        socket.inet_pton(socket.AF_INET6, addr)
    except socket.error:
        return False
    return True