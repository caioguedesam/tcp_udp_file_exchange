import random as rd
import socket

LOSS_P = 0.75

def send(packet, sock, addr):
    if rd.uniform(0, 1) <= LOSS_P:
        sock.sendto(packet, addr)
    else:
        print('Lost packet')