import os
import socket
import pickle
import sys
from datetime import datetime
from os import getlogin
from threading import Thread
from time import sleep
import logging
from client_utils import plots_available, get_local_ip, get_plots_path

# Configure logger
level = logging.INFO
format = '%(asctime)s::%(name)s::%(levelname)s: %(message)s'

logger = logging.getLogger()

now = datetime.now()
handler = logging.FileHandler(f'./logs/log_{now.month}M_{now.day}D_{now.hour}H_{now.minute}M_{now.second}S.txt')
handler.setLevel(level)
formatter = logging.Formatter(format)
handler.setFormatter(formatter)

logger.addHandler(handler)

USERNAME = getlogin()
BUFFER_SIZE = 64


def send(sock, data):
    try:
        sock.sendall(data)
        return 1
    except socket.error:
        return 0


def plots_info_socket(port):
    plots_path = get_plots_path()
    my_ip = get_local_ip()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((my_ip, port))
        logger.info('waiting for connection...')
        sock.listen()
        conn, addr = sock.accept()
        logger.info(f'connection established')
        while True:
            plots_avlb = plots_available(plots_path)
            msg = (USERNAME, plots_avlb)
            encoded_msg = pickle.dumps(msg)
            if send(conn, encoded_msg) == 0:
                logger.info('***server down***')
                logger.info(f'closing connection on p: {port}')
                conn.close()
                open_register_client()
                return

            logger.info(f"sent: {plots_avlb}")
            sleep(1)


def open_register_client():
    t = Thread(target=register_client)
    t.start()


def open_tcp_listener(port):
    t = Thread(target=plots_info_socket, args=(port,))
    t.start()


def connect(sock, addr):
    while True:
        try:
            sock.connect(addr)
            break
        except socket.error:
            logger.error(f"trying to reach server on p: {TCP_PORT}")
            sleep(1)


def register_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect(sock, SERVER_ADDR)
    msg = pickle.dumps(USERNAME)
    sock.sendall(msg)
    logger.info(f'request to join sent')
    port = sock.recv(BUFFER_SIZE)

    port_decoded = pickle.loads(port)
    logger.info(f'received port: {port_decoded}')

    open_tcp_listener(port_decoded)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"usage: {os.path.basename(__file__)} <host> <port>")
        sys.exit(1)

    # TCP_IP = "192.168.1.20"
    # TCP_PORT = 60021
    TCP_IP, TCP_PORT = sys.argv[1:]
    SERVER_ADDR = (TCP_IP, int(TCP_PORT))

    register_client()
