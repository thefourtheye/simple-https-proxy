from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
from connection import ConnectionHandler
import sys

server_socket, connections = socket(AF_INET, SOCK_STREAM), []
try:
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(('', 8000))
    server_socket.listen(5)

    while True:
        connections.append(ConnectionHandler(*server_socket.accept()))
        connections[-1].start()

except (OSError, KeyboardInterrupt, TypeError, ValueError, StopIteration) as err:
    if isinstance(err, OSError) and err.errno == 98:
        sys.stderr.write("Port 8000 is open")
    else:
        sys.stderr.write(str(err))
        print("Closing Server Socket")
        server_socket.shutdown(SHUT_RDWR)
        server_socket.close()
finally:
    for connection in connections:
        connection.close()