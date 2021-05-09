import logging
import os
import sys
import tkinter as tk
import queue
from ctypes import windll
from server import register_server
from threading import Thread
from server.server_utils import RemoteHostBox
from datetime import datetime

level = logging.INFO
format = '%(asctime)s::%(name)s::%(levelname)s: %(message)s'

logger = logging.getLogger()

now = datetime.now()
handler = logging.FileHandler(f'./server/logs/log_{now.month}M_{now.day}D_{now.hour}H_{now.minute}M_{now.second}S.txt')
handler.setLevel(level)
formatter = logging.Formatter(format)
handler.setFormatter(formatter)

logger.addHandler(handler)

user32 = windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)


class GUI:
    def __init__(self):
        # Window init and config
        self.root = tk.Tk()
        self.root.title("Plots Available")
        self.root.geometry(f"300x300-{screen_width - 310}+0")
        self.root.configure(background='#181818')
        self.root.columnconfigure(1, weight=2)

        # Additional Data
        self.remote_hosts_data = {}
        self.last_used_row = 0
        self.queue = queue.Queue()

        self.order_connections_boxes()
        self.start_server()
        self.queue_listener()

        self.root.mainloop()

    def order_connections_boxes(self):
        sorted_boxes = sorted(self.remote_hosts_data.items(), key=lambda box: box[1].hostname)
        i = 0
        for _, box in sorted_boxes:
            box.update(i)
            i += 1

        self.root.after(50, self.order_connections_boxes)

    def queue_listener(self):
        if not self.queue.empty():
            socket_info = self.queue.get_nowait()
            self.accept_req(socket_info)

        self.root.after(500, self.queue_listener)

    def accept_req(self, socket_info):
        username, _ = socket_info
        if username in self.remote_hosts_data:
            self.update_remote_host(socket_info)
            return

        box = RemoteHostBox(self.root, socket_info, logger)
        box.show(self.last_used_row)
        self.remote_hosts_data[username] = box
        self.last_used_row += 1

    def update_remote_host(self, socket_info):
        username, addr_info = socket_info
        remote_host_box = self.remote_hosts_data[username].remote_host

        ip, port = addr_info
        if not remote_host_box.ip == ip:
            remote_host_box.change_ip(ip)
            logger.info(f'changed ip on {username} from {remote_host_box.ip} to {ip}')

        remote_host_box.change_port(port)
        logger.info(f'changed port on {username} from {remote_host_box.port} to {port}')

        remote_host_box.connect()

    def start_server(self):
        t1 = Thread(target=register_server.start_server, args=(SERVER_ADDR, self.queue, logger,))
        t1.setDaemon(True)
        t1.start()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"usage: {os.path.basename(__file__)} <host> <port>")
        sys.exit(1)

    # TCP_IP = "192.168.1.20"
    # TCP_PORT = 60021
    TCP_IP, TCP_PORT = sys.argv[1:]
    SERVER_ADDR = (TCP_IP, int(TCP_PORT))

    GUI()
