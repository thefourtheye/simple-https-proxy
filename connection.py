from threading import Thread
from http_stream_handler import HTTPStreamHandler
from gen_ca_cert import gen_cert
from http_request_parser import HTTPRequest, HTTPRequestException
import OpenSSL
import socket
import urllib.request


class ConnectionHandler(Thread):
    def __init__(self, client_socket, _):
        super(ConnectionHandler, self).__init__()
        self.is_secure, self.is_closed, self.context = False, False, {}
        self.socket, self.stream, self.request = None, None, None
        self.set_socket(client_socket)

    def set_socket(self, socket_object, is_ssl=False):
        self.socket, self.is_secure = socket_object, is_ssl
        self.stream = HTTPStreamHandler(self.socket, self.is_secure)

    def switch_to_https(self):
        self.stream.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
        # print("Just Sent the connection established message")
        key, cert = gen_cert(self.request.get_host())
        server_context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
        server_context.use_privatekey(key)
        server_context.use_certificate(cert)
        server_ssl = OpenSSL.SSL.Connection(server_context, self.socket)
        server_ssl.set_accept_state()
        server_ssl.do_handshake()
        self.set_socket(server_ssl, True)

    def run(self):
        try:
            self.request = HTTPRequest(self.stream)
        except HTTPRequestException:
            return self.stream.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")

        if self.request.get_method() == "CONNECT":
            self.switch_to_https()
            self.request = HTTPRequest(self.stream, True)

        if self.request.get_method() in {"GET", "POST", "DELETE", "PUT"}:
            print(self.request.get_url())
            try:
                f = urllib.request.urlopen(self.request.get_url())
                response = f.read()
                self.stream.send(response)
            except urllib.error.HTTPError as e:
                print("Failed: {}, Code: {}".format(self.request.get_url(), e.code))
                self.stream.send(str.encode("{} {}".format(self.request.get_version(), e.code)))
            # self.stream.send(str.encode("HTTP/1.1 200 OK\r\n\r\n<h2>GET {}</h2>".format(self.request.get_url())))
        else:
            self.stream.send(b"HTTP/1.1 400 Unknown HTTP Verb\r\n\r\n")
        self.close()

    def close(self):
        if not self.is_closed:
            # print("Closing the Client Socket")
            self.is_closed = True
            self.stream.close()
            if self.is_secure:
                self.socket.shutdown()
                self.socket.sock_shutdown(socket.SHUT_WR)
            else:
                self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()

    def __del__(self):
        if hasattr(self, "is_closed") and not self.is_closed:
            self.close()
