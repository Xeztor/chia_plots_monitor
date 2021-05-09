import json
import logging
import socket
import sys
from os import listdir

BUFFER_SIZE = 64

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


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


def get_plots_path():
    with open('./plots_path.txt', 'r') as file:
        data = json.load(file)
    path = data['path']
    return path


def plots_available(plots_path):
    plots = 0
    files = listdir(plots_path)
    for filename in files:
        if '.plot' in filename:
            plots += 1

    return plots
