import logging
import pickle
import queue
import socket
import sys
import tkinter as tk
from copy import deepcopy
from threading import Thread

COLORS = {'fg': 'white', 'bg': '#181818'}
max_wait_iters_for_response = 20

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

BUFFER_SIZE = 64


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def open_connection(ip, port, queue, logger):
    def close_connection(sock, addr):
        sock.close()
        logger.info(f'socket on p:{addr[1]} for ip:{addr[0]} closed')

    def connect(sock, addr):
        sock.connect(addr)
        logger.info(f"connection established. client: {addr_pair}")

    addr_pair = (ip, port)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            connect(sock, addr_pair)
        except socket.error:
            close_connection(sock, addr_pair)

        while True:
            try:
                data = sock.recv(BUFFER_SIZE)
            except socket.error as err:
                logger.error(str(err))
                close_connection(sock, addr_pair)
                break

            username, plots_avlb = pickle.loads(data)
            logger.debug(f'recieved: {plots_avlb} ({username})')
            queue.put(plots_avlb)


class RemoteHostBox:
    MAX_SECONDS_TIMEOUT = 10

    def __init__(self, root, sock_info, logger):
        username, sock_addr = sock_info
        self.__iters_no_connection = 0
        self.__queue = queue.Queue()
        self.__logger = logger
        self.remote_host = sock_addr
        self.secs_not_connected = 0

        self.hostname = username
        self.root = root

        self.name_label = tk.Label(self.root, text=f"{self.hostname}: ", font='arial 14', anchor='e', **COLORS)
        self.plots_available = tk.Label(self.root, text=f"Plots Available: ", anchor='center', font='arial 9',
                                        **COLORS)

        self.widgets = [self.name_label, self.plots_available]

        self.remote_host.connect()
        self.receive_plots_count_listener()

    @property
    def remote_host(self):
        return self.__remote_host

    @remote_host.setter
    def remote_host(self, socket_info):
        ip = socket_info[0]
        port = socket_info[1]
        self.__remote_host = RemoteHostListener(ip, port, self.__queue, self.__logger)

    def show(self, row):
        self.name_label.grid(row=row, column=0, sticky='ewns')
        self.plots_available.grid(row=row, column=1, sticky='ew')

    def remove_box_from_screen(self):
        for widget in self.widgets:
            widget.destroy()

    def update(self, row):
        old = {}
        for widget in self.widgets:
            widget_info = widget.grid_info()
            widget_info['row'] = row
            old[widget] = widget_info

        # self.remove_box_from_screen()

        for obj, kwargs in old.items():
            obj.grid(**kwargs)

    def reconnect(self):
        self.plots_available.config(text="Trying to reconnect...", font='arial 9', fg='white', bg='#c94f4f')

    def receive_plots_count_listener(self):
        if not self.__queue.empty():
            plots_count = self.__queue.get_nowait()
            self.plots_available.config(text=f"Plots Available: {plots_count}", **COLORS)
            self.secs_not_connected = 0

        if self.secs_not_connected > RemoteHostBox.MAX_SECONDS_TIMEOUT:
            self.reconnect()
            self.secs_not_connected = 0

        self.secs_not_connected += 1
        self.root.after(1000, self.receive_plots_count_listener)


class RemoteHostListener:

    def __init__(self, ip, port, queue, logger):
        self.ip = ip
        self.port = port
        self.queue = queue
        self.is_connected = True
        self.logger = logger

    def connect(self):
        t = Thread(target=open_connection, args=(self.ip, self.port, self.queue, self.logger,))
        t.setDaemon(True)
        t.start()

    def change_port(self, port):
        self.port = port

    def change_ip(self, ip):
        self.ip = ip
