# Based on the example found at
# https://github.com/pyca/pyopenssl/blob/de0a71ec331102c4c5bb1470752e992cc85d731b/examples/certgen.py

"""
Certificate generation module.
"""

from OpenSSL import crypto
from hashlib import md5
DIGEST_ALGORITHM = "sha1"


def gen_key_pair():
    """
    Create a public/private key pair.

    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)
    return pkey


def gen_cert_request(pkey, name):
    """
    Create a certificate request.

    Arguments: pkey   - The key to associate with the request
               name   - The name of the subject of the request
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()
    setattr(req.get_subject(), "CN", name)

    req.set_pubkey(pkey)
    req.sign(pkey, DIGEST_ALGORITHM)
    return req


def _gen_cert(req, issuer_cert, issuer_key):
    """
    Generate a certificate given a certificate request.

    Arguments: req         - Certificate request to use
               issuer_cert - The certificate of the issuer
               issuer_key  - The private key of the issuer
    Returns:   The signed certificate in an X509 object
    """
    cert = crypto.X509()
    from OpenSSL import rand
    serial_number = int.from_bytes(rand.bytes(16), byteorder='big')
    # print(serial_number)

    # hash_value = md5(req.get_subject().get_components()[0][1]).digest()
    # serial_number = int.from_bytes(hash_value, byteorder='big')
    # print(serial_number, req.get_subject().get_components()[0][1])

    cert.set_serial_number(serial_number)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(100*365*24*60)
    cert.set_issuer(issuer_cert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuer_key, DIGEST_ALGORITHM)
    return cert


def gen_cert(name, certs={}):
    if name not in certs:
        key = gen_key_pair()
        req = gen_cert_request(key, name)
        issuer_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open("ssl/server.crt").read())
        issuer_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open("ssl/server.key").read())
        certs[name] = (key, _gen_cert(req, issuer_cert, issuer_key))
    return certs[name]
