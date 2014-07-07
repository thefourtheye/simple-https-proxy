from listener import serve
from pprint import pprint


def handle_responses(request, response):
    pprint(response)

serve({}, handle_responses)
