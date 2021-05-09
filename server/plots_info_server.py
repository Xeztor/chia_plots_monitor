import select
import socket
import pickle
import logging
import sys
from queue import Queue


def reconncet():
    pass


def open_connection(ip, port, queue):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((ip, port))
        except Exception:
            queue.put('reconnect')
            reconncet()
        print(f"connection established.")
        while True:
            data = sock.recv(64)
            plots_avlb = pickle.loads(data)
            print(f'recieved: {plots_avlb}')
            queue.put(plots_avlb)


if __name__ == '__main__':
    open_connection("192.168.1.20", 60000, Queue())
