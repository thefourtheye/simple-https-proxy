from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
from connection import ConnectionHandler
import sys


def serve(options=None, interceptor=None):
    if not isinstance(options, dict):
        print("Options is not a dictionary. Ignoring it")
        options = {}

    ip, port = options.get("ip", ""), options.get("port", 8000)

    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind((ip, port))
        server_socket.listen(5)

        while True:
            ConnectionHandler(*server_socket.accept()).service(interceptor)

    except (OSError, KeyboardInterrupt, TypeError, ValueError) as err:
        if isinstance(err, OSError) and err.errno == 98:
            sys.stderr.write("Port 8000 is open")
        else:
            sys.stderr.write(str(err))
    finally:
        print("Closing Server Socket")
        server_socket.shutdown(SHUT_RDWR)
        server_socket.close()