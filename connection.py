from http_stream_handler import HTTPStreamHandler
from gen_ca_cert import gen_cert
from http_request_parser import HTTPRequest, HTTPRequestException
import OpenSSL
import socket
import urllib.request
import urllib.error
import requests


class ConnectionHandler:
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

    def service(self, interceptor):
        try:
            self.request = HTTPRequest(self.stream)
        except HTTPRequestException:
            return self.stream.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")

        if self.request.get_method() == "CONNECT":
            self.switch_to_https()
            self.request = HTTPRequest(self.stream, True)

        print(self.request.get_url(), self.request.get_method())
        if self.request.get_method() in {"GET", "POST", "DELETE", "PUT", "PATCH"}:
            try:
                from pprint import pprint
                http_method = getattr(requests, self.request.get_method().lower())
                result = http_method(self.request.get_url(), data=self.request.body,
                                     headers=self.request.get_headers(),
                                     allow_redirects=False, timeout=10)

                if result.status_code < 200 or result.status_code > 399:
                    pprint(result.status_code)

                if 'content-security-policy' in result.headers:
                    pprint(result.headers['content-security-policy'].split())

                if 300 <= result.status_code < 400:
                    pprint("Being redirected")
                    pprint(self.request.get_url())
                    pprint(dict(result.headers))

                interceptor(self.request, result.content + str.encode("\r\n"))
                self.stream.send(result.content + str.encode("\r\n"))
            except urllib.error.HTTPError as e:
                print("Failed: {}, Code: {}".format(self.request.get_url(), e.code))
                self.stream.send(str.encode("{} {}"
                                            .format(self.request.get_version(), e.code)))
            except OSError as e:
                pprint(e)
                print("Failed: {}, Code: {}".format(self.request.get_url(), 408))
                self.stream.send(str.encode("{} 408\r\n\r\n"
                                            .format(self.request.get_version())))
        else:
            self.stream.send(b"HTTP/1.1 400 Unknown HTTP Verb\r\n\r\n")
        self.close()

    def close(self):
        if not self.is_closed:
            # print("Closing the Client Socket")
            try:
                self.is_closed = True
                self.stream.close()
                if self.is_secure:
                    self.socket.shutdown()
                    self.socket.sock_shutdown(socket.SHUT_WR)
                else:
                    self.socket.shutdown(socket.SHUT_WR)
            except OpenSSL.SSL.Error as e:
                print(e)
            self.socket.close()

    def __del__(self):
        if hasattr(self, "is_closed") and not self.is_closed:
            self.close()
