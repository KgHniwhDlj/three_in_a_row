import socket
import time

from logger import logger


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def find_server_by_port(port):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        udp.bind(("", port))
    except OSError as e:
        logger.error(f"Ошибка при привязке к порту {port}: {e}")
        return None, None

    timeout = time.time() + 15
    while time.time() < timeout:
        try:
            udp.settimeout(5)
            data, addr = udp.recvfrom(1024)
            code, ip, srv_port = data.decode().split(":")
            if code == str(port):
                return ip, int(srv_port)
        except socket.timeout:
            continue

    return None, None
