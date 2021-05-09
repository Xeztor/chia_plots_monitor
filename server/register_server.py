import logging
import pickle
import queue
import socket
from collections import defaultdict

BUFFER_SIZE = 64


def start_server(server_addr, queue, logger):
    class PortPool:
        def __init__(self, start, stop):
            self.free = [*range(start, stop + 1)]
            self.taken = []

        def get(self):
            if not self.free:
                logger.info('No port available')

            port = self.free.pop(self.free.index(min(self.free)))
            self.taken.append(port)
            return port

        def close_port(self, port):
            if port not in self.taken:
                logger.info('Port isn\'t in use')

            self.taken.remove(port)
            self.free.append(port)

    port_pool = PortPool(60000, 60020)

    connections_info = defaultdict(int)
    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_STREAM)  # TCP
    sock.bind(server_addr)

    logger.info(f"Server is up listening on port {server_addr[1]}")
    while True:
        sock.listen()
        conn, addr = sock.accept()
        with conn:
            data = conn.recv(BUFFER_SIZE)
            username = pickle.loads(data)
            logger.info(f"received req from: {username} ip:{addr[0]} port: {addr[1]}")

            if username in connections_info:
                port = connections_info[username]
                port_pool.close_port(port)
                logger.info(f'port: {port} released')

            free_port = port_pool.get()
            target_addr = (addr[0], free_port)
            sock_info = (username, target_addr)

            connections_info[username] = free_port

            port_encoded = pickle.dumps(free_port)
            conn.sendall(port_encoded)
            queue.put(sock_info)
            logger.info(f"sent port: {free_port}---reciever:{username} ip:{addr[0]} p:{addr[1]}")


if __name__ == '__main__':
    start_server(("192.168.1.20", 60021), queue.Queue(), logging.getLogger())
