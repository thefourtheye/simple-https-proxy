from threading import Thread
from reader import HTTPStreamReader
import OpenSSL
from gen_ca_cert import gen_cert


class ConnectionHandler(Thread):

    def __init__(self, client_socket, client_addr):
        super(ConnectionHandler, self).__init__()
        self.socket, self.addr, self.context = client_socket, client_addr, {}
        self.r_stream = HTTPStreamReader(self.socket.makefile(mode='rb', buffering=0))
        self.w_stream = self.socket.makefile(mode='wb', buffering=0)
        self.closing = False

    def send_to_client(self, data):
        if hasattr(self.w_stream, 'sendall'):
            print("Sending All...", data)
            self.w_stream.sendall(data)
        elif hasattr(self.w_stream, 'send'):
            print("Sending...", data)
            self.w_stream.send(data)
        elif hasattr(self.w_stream, 'write'):
            print("Writing...", data)
            self.w_stream.write(data)
            if hasattr(self.w_stream, 'flush'):
                print("Flushing...", data)
                self.w_stream.flush()

    def get_context_from_request(self):
        request_line = self.r_stream.get_http_line().decode("utf-8").rstrip("\r\n")
        print(request_line)
        parts = request_line.split()
        if len(parts) != 3:
            return "bad"
        self.context["method"], self.context["server"], self.context["version"] = parts
        parts, self.context["port"] = str(self.context["server"]).rsplit(":", 1), "80"
        if len(parts) == 2 and parts[1].isdigit():
            self.context["server"], self.context["port"] = parts
        print(self.context)

    def run(self):
        if self.get_context_from_request() == "bad":
            return self.send_to_client("HTTP/1.1 400 Bad Request\r\n")

        print(self.r_stream.get_all_data())
        if self.context["method"] == "CONNECT":
            self.send_to_client(b"HTTP/1.1 200 Connection established\r\n\r\n")
            print("Just Sent the connection established message")
            key, cert = gen_cert(self.context["server"])
            server_context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
            # server_context.use_privatekey(OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, open("ssl/server.key").read()))
            # server_context.use_certificate(OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, open("ssl/server.crt").read()))
            server_context.use_privatekey(key)
            server_context.use_certificate(cert)
            server_ssl = OpenSSL.SSL.Connection(server_context, self.socket)
            server_ssl.set_accept_state()
            server_ssl.do_handshake()
            self.w_stream = server_ssl
            self.r_stream = HTTPStreamReader(server_ssl)
            print(self.r_stream.get_all_data())
            self.send_to_client(b"HTTP/1.1 200 OK\r\n\r\n<h1>Welcome</h1>")
            print(self.r_stream.get_all_data())
        else:
            self.send_to_client(b"HTTP/1.1 200 OK\r\n\r\n<h1>Welcome</h1>")
            self.close()

    def close(self):
        print("Closing the Client Socket")
        self.closing = True
        self.w_stream.close()
        self.r_stream.close()
        self.socket.close()

    def __del__(self):
        if not self.closing:
            self.close()
