"""PKI stuff"""
import OpenSSL.crypto
import pem

def make_p12(cert_file, key_file):
    """Convert cert/key files to OpenSSL p12 object"""
    c = open(cert_file, 'rt').read()
    k = open(key_file, 'rt').read()
    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, c)
    key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, k)
    p12 = OpenSSL.crypto.PKCS12()
    p12.set_certificate(cert)
    p12.set_privatekey(key)
    return p12

def get_dns_sans(cert):
    for i in range(cert.get_extension_count()):
        if cert.get_extension(i).get_short_name() == 'subjectAltName':
            sans = str(cert.get_extension(i)).split(', ')
            return [ x[4:] for x in sans if x[:4]=="DNS:" ]
    return []

def pack_l2s(lnum, sep='', case='lower'):
    import ctypes
    PyLong_AsByteArray = ctypes.pythonapi._PyLong_AsByteArray
    PyLong_AsByteArray.argtypes = [ctypes.py_object,
                                   ctypes.c_char_p,
                                   ctypes.c_size_t,
                                   ctypes.c_int,
                                   ctypes.c_int]
    a = ctypes.create_string_buffer(lnum.bit_length()//8 + 1)
    PyLong_AsByteArray(lnum, a, len(a), 0, 1)
    hexbytes = ["{:02x}".format(ord(b)) for b in a.raw]
    while hexbytes[0] == '00':
        hexbytes.pop(0)
    if case == 'upper':
        return sep.join(hexbytes).upper()
    return sep.join(hexbytes)

class certs_from_pemfile():
    import OpenSSL.crypto
    import pem
    def __init__(self, pemfile):
        self.certs = pem.parse_file(pemfile)
        for i in range(len(self.certs)):
            self.certs[i] = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, str(self.certs[i]))

    def __len__(self):
        return self.len()

    def len(self):
        return len(self.certs)

    def prune_root(self):
        for i in list(reversed(range(len(self.certs)))):
            if self.certs[i].get_issuer() == self.certs[i].get_subject():
                self.certs.pop(i)
                return True
        return False

    def get_cert(self,i):
        return self.certs[i]

    def get_all_certs(self):
        return self.certs

    def get_cert(self,i):
        return self.certs[i]

    def prune_not_ca(self):
        from pyasn1.codec.ber import decoder as d
        for i in list(reversed(range(len(self.certs)))):
            for e in range(self.certs[i].get_extension_count()):
                if self.certs[i].get_extension(e).get_short_name() == 'basicConstraints':
                    data = d.decode(self.certs[i].get_extension(e).get_data())[0]
                    ca = False
                    if data:
                        ca = data.getComponentByPosition(0)
                    if not ca:
                        self.certs.pop(i)
                        return True
        return False

    def get_server_cert(self):
        from pyasn1.codec.ber import decoder as d
        for i in range(len(self.certs)):
            for e in range(self.certs[i].get_extension_count()):
                if self.certs[i].get_extension(e).get_short_name() == 'basicConstraints':
                    data = d.decode(self.certs[i].get_extension(e).get_data())[0]
                    ca = False
                    if data:
                        ca = data.getComponentByPosition(0)
                    if not ca:
                        return self.certs[i]
