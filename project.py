import configparser
import pickle
import sys
import socket
import select
import secrets
import hashlib

import gensafeprime

from IPython import embed

import socket
import struct
import pickle

SECURITY_PARAMETER = 128 #bits
TOKEN_PADDING = 128

def collisionResistantHash(x):
    return int(hashlib.md5(x).hexdigest(), 16)

class BasicSocket():
    def __init__(self, is_server, port, ip="0.0.0.0"):
        self._setup(is_server, port, ip)

    def _setup(self, is_server, port, ip):
        self.socket = None
        self.is_server = is_server
        self.port = port
        self.ip = ip
        if self.is_server:
            self._waitForConnection()
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(1)
            target = (self.ip, self.port)
            self.socket.connect(target)

    def _waitForConnection(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #make sure that we can re-connect quickly
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            serversocket.bind(("0.0.0.0", self.port))
        except OSError:
            print('FATAL ERROR: Could not bind to port. You must terminate the program.')
            return
        serversocket.listen(5)
        live_sockets = [serversocket,]
        readable, writeable, exceptional = select.select(live_sockets, [], live_sockets)
        for s in readable:
            if s == serversocket:
                client, address = s.accept()
                self.socket = client

    def getMessage(self):
        size_byte_str = self.socket.recv(4)
        if len(size_byte_str) == 0:
            return None
        size = struct.unpack("<I", size_byte_str)[0]
        byte_str = self.socket.recv(size)
        return byte_str

    def sendMessage(self, byte_str):
        msg_len = len(byte_str)
        msg_len_str =  struct.pack("<I", msg_len)
        r = self.socket.send(msg_len_str)
        r = self.socket.send(byte_str)
        return r

class AuthSocket():
    def __init__(self, config, config_file):
        self._load_cert(config, config_file)

        ip = config.get('General', 'server_ip')
        port = config.getint('General', 'server_port')
        is_server = config.getboolean('General', 'is_server')
        self.basic_socket = BasicSocket(is_server, port, ip)

    def _load_cert(self, config, config_file):
        my_cert_file = config.get('General', 'my_cert_file')
        my_cert_config = loadFile(my_cert_file)
        cert_e = my_cert_config.getint('General', 'e', fallback=-1)
        if cert_e == -1:
            #generate our certificate file
            p, q, e, d, N, phi = getRSA()
            my_cert_config.add_section('General')
            my_cert_config.set('General', 'e', str(e))
            my_cert_config.set('General', 'N', str(N))
            with open(my_cert_file, 'w') as f:
                my_cert_config.write(f)
            config.set('General', 'my_cert_key', str(d))
            with open(config_file, 'w') as f:
                config.write(f)

        mac_key = config.getint('General', 'my_cert_key', fallback=-1)
        mac_N = my_cert_config.getint('General', 'N', fallback=-1)

        remote_cert_file = config.get('General', 'remote_cert_file')
        remote_cert_config = loadFile(remote_cert_file)

        cert = remote_cert_config.getint('General', 'e', fallback=-1)
        cert_N = remote_cert_config.getint('General', 'N', fallback=-1)

        if cert == -1:
            raise ValueError("ERROR! THE REMOTE CERT DOES NOT SEEM TO HAVE THE CORRECT VALUES!")
        self.mac_key = mac_key
        self.mac_N = mac_N
        self.cert= cert
        self.cert_N = cert_N

    def getMessage(self):
        byte_str = self.basic_socket.getMessage()
        token_str = byte_str[0:TOKEN_PADDING]
        token = int(token_str)
        msg = byte_str[TOKEN_PADDING:]
        msg_hash = collisionResistantHash(msg)
        if msg_hash != pow(token, self.cert, self.cert_N):
            print("ERROR! MAC HAS FAILED!!!!")
            return
        else:
            return msg

    def sendMessage(self, msg_str):
        format_str = "{{:0{}d}}".format(TOKEN_PADDING)
        msg_hash = collisionResistantHash(msg_str)
        token = pow(msg_hash, self.mac_key, self.mac_N)
        # IF THIS IS FAILING, INCREASE TOKEN_PADDING
        assert len(str(token)) <= TOKEN_PADDING
        token_str = format_str.format(token).encode()
        byte_str = token_str+msg_str
        r = self.basic_socket.sendMessage(byte_str)
        return r



# Thanks: https://stackoverflow.com/questions/4798654/modular-multiplicative-inverse-function-in-python
def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

def RSAGeneratePrimes(n):
    p = gensafeprime.generate(n)
    q = gensafeprime.generate(n)
    return (p, q)

def loadFile(f):
    config = configparser.RawConfigParser()
    config.read(f)
    return config

def saveToFile(loc, config):
    f = open(loc, "w")
    config.write(f)
    f.close()

def getRSA():
    p, q = RSAGeneratePrimes(SECURITY_PARAMETER)
    N = p*q
    phi = (p-1)*(q-1)
    e = -1
    d = -1
    while True:
        try:
            e = secrets.randbelow(N)
            #NOTE: If e is not coprime with phi, this will except and we will re-try
            d = modinv(e, phi)
            break
        except:
            continue

    assert pow(pow(1234, d, N), e, N) == 1234
    # This concludes our testing
    return (p, q, e, d, N, phi)

# Let's Authenticate!
def runServer(config, config_file):
    """
    go through and hash all files

    1)
    create a new public and private key
    encrypt each file's hash with the public key
    send a pickle.dumps([public_key, enc_file_1, enc_file_2, ....])

    2)
    receive a similar object, then re-encrypt each hash with the new pub key,
    compare each of those received encrypted hashses with the ecryptions of your own hashes

    To write the client code, do these two steps in oposite order


    No need to add any other layer of security, the pub-key crypto here already hides things.
    """
    s = AuthSocket(config, config_file)
    msg = 'Test'.encode()
    s.sendMessage(msg)

def runClient(config, config_file):
    s = AuthSocket(config, config_file)
    msg = s.getMessage()
    embed()

def main():
    if len(sys.argv) < 2:
        print('Usage: '+sys.argv[0]+' config-file')
        sys.exit(1)

    config_file = sys.argv[1]
    config = loadFile(config_file)

    is_server = config.getboolean('General', 'is_server')


    if is_server:
        runServer(config, config_file)
    else:
        runClient(config, config_file)



if __name__ == "__main__":
    main()
