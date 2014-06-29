class HTTPStreamReader:
    def __init__(self, object):
        self.r = object
        if hasattr(object, "read"):
            self.read = object.read
        else:
            self.read = object.recv

    def get_http_line(self):
        return next(self.r)

    def get_data(self, size=4096):
        return self.read(max(1, min(size, 4096)))

    def get_all_data(self):
        size, result = 4096, ""
        while True:
            data = str(self.read(size))
            result += data
            if len(data) < size:
                break
        return result

    def close(self):
        print("Closing the Client Connection")
        self.r.close()