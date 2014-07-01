class HTTPRequestException(Exception):
    def __init__(self, message):
        self.message = message


class HTTPRequest:

    def __init__(self, stream, is_secure=False):
        self.context, self.body, self.headers = {}, "", {}
        self.is_secure, self.raw_request = is_secure, ""
        self.parse_request(stream)

    def get_context(self, request_line):
        # print(request_line)
        parts = request_line.split()
        if len(parts) != 3:
            raise HTTPRequestException("Invalid HTTP Request line")
        self.context["method"], self.context["resource"], self.context["version"] = parts
        parts, self.context["port"] = str(self.context["resource"]).rsplit(":", 1), "80"
        if len(parts) == 2 and parts[1].isdigit():
            self.context["resource"], self.context["port"] = parts
        # print(self.context)

    def parse_request(self, stream):
        self.raw_request = stream.get_all_data()
        # print(self.raw_request)
        splitted_request = self.raw_request.split("\r\n", 1)
        if len(splitted_request) == 2:
            request_line, rest = splitted_request
        else:
            request_line, rest = splitted_request[0], ""
        self.get_context(request_line)
        headers, header_section, body = {}, True, []
        for line in rest.split("\r\n"):
            if (": " in line) and header_section:
                header, value = line.split(": ", 1)
                headers[header] = value
            elif line == "" or line == "\r\n":
                header_section = False
            elif header_section:
                raise HTTPRequestException("Bad HTTP Request")
            else:
                body.append(line)
        self.headers, self.body = headers, "\r\n".join(body)

        self.get_host()
        port = ":{}".format(self.get_port()) if self.get_port() != "80" else ""
        if self.get_resource().startswith("/"):
            self.context["url"] = "{}://{}{}{}".format(self.get_protocol(),
                                                       self.get_host(),
                                                       port,
                                                       self.get_resource())
        elif self.get_resource().startswith(self.get_protocol()):
            self.context["url"] = "{}{}".format(self.get_resource(), port)
        else:
            self.context["url"] = "{}://{}{}".format(self.get_protocol(),
                                                     self.get_resource(), port)

    def get_protocol(self):
        return "https" if self.is_secure else "http"

    def get_method(self):
        return self.context.get("method", "")

    def get_resource(self):
        return self.context.get("resource", "")

    def get_version(self):
        return self.context.get("version", "")

    def get_port(self):
        return self.context.get("port", "")

    def get_host(self):
        data = self.headers.get("Host", None)
        if data is not None and ":" in data:
            host, port = data.rsplit(":")
            if port.isdigit():
                self.headers["Host"] = host
                self.context["port"] = port
                data = host
        return data

    def get_url(self):
        return self.context.get("url", "")

    def get_headers(self):
        return self.headers