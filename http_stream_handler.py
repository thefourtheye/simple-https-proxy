class HTTPStreamHandler:
    def __init__(self, socket_object, is_secure):
        self.s, self.is_secure = socket_object, is_secure
        if is_secure:
            self.reader, self.writer = self.s, self.s
        else:
            self.reader = self.s.makefile(mode='rb', buffering=0)
            self.writer = self.s.makefile(mode='wb', buffering=0)

        if hasattr(self.reader, "read"):
            self.read = self.reader.read
        else:
            self.read = self.reader.recv

    def get_http_line(self):
        if not self.is_secure:
            result = next(self.reader, b"")
        else:
            result, temp = b"", " "
            while temp != "" and result[-2:] != b"\r\n":
                temp = self.get_data(1)
                result += temp
        return result.decode("utf-8").rstrip("\r\n")

    def get_data(self, size=4096):
        return self.read(max(1, min(size, 4096)))

    def get_all_data(self):
        size, result = 4096, ""
        while True:
            data = self.read(size).decode("utf-8")
            result += data
            if len(data) < size:
                break
        return result

    def send(self, data):
        # print("Sending...", data)
        if hasattr(self.writer, 'sendall'):
            self.writer.sendall(data)
        elif hasattr(self.writer, 'send'):
            self.writer.send(data)
        elif hasattr(self.writer, 'write'):
            self.writer.write(data)
        if hasattr(self.writer, 'flush'):
            self.writer.flush()

    def write(self, data):
        self.send(data)

    def close(self):
        if not self.is_secure:
            self.reader.close()
            self.writer.close()