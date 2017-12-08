import socket
import struct
import pickle

# returns None if the connection was terminated, received object otherwise
# s = Socket()
def getMessage(s):
    try:
        size_byte_str = s.recv(4)
        if len(size_byte_str) == 0:
            return None
        size = struct.unpack("<I", size_byte_str)[0]
        byte_str = s.recv(size)
    except ConnectionResetError:
        return None
    obj = pickle.loads(byte_str)
    return obj

# attempts to send a python object over a socket
# s = Socket()
# obj = python object
def sendMessage(s, obj):
    obj_str = pickle.dumps(obj)
    msg_len = len(obj_str)
    msg_len_str =  struct.pack("<I", msg_len)
    r = s.send(msg_len_str)
    r = s.send(obj_str)
    return r

# This will return a socket connected to target
# target = (str(ip), int(port))
def doConnect(target):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect(target)
    except socket.error as serr:
        if serr.errno == errno.ECONNREFUSED:
            print(target, 'connection error: Connection refused by server')
        elif serr.errno == errno.ENOEXEC:
            print(target, 'connection error: Exec format error (maybe the server you specified doesn\'t exist, or you have a problem connecting to the Internet)')
        else:
            print(target, 'connection error:',serr.errno)
        return None
    return s

def doSelect(liveSockets, t=1.0, severSocket=None, handleFunction=None):
    if len(liveSockets) == 0:
        print("Error: doSelect received an empty liveSockets")
        return None
    while True:
        if len(liveSockets) == 0:
            print("Error: doSelect liveSockets is now empty")
            return None

        readable, writeable, exceptional = select.select(liveSockets, [], liveSockets, t)
        if len(readable) == 0:
            # We timed out out
            return None

        for s in readable:
            if serverSocket not None and serverSocket == s:
                client, address = s.accept()
                liveSockets.append(client)
                continue
            receipt = getMessage(s)
            if receipt is not None:
                # Check to see if we're supposed to return or call a handler
                if handleFunction != None:
                    handleFunction(client, receipt)
                else:
                    return receipt
            else:
                # Get Message returned None, socket failed
                liveSockets.remove(s)

# wrapper around send, will try to send msg to socket or ip:port
# if we aren't currently connected we will try to connect
# will return tuple (Socket, sentBytes)
def sendWrap(s, obj, ip=None, port=None):
    if s == None:
        s = doConnect(remotes[to_id])

    # If it's still None, we failed to connect again, return -1
    if s == None:
        return (None, -1)
    try:
        # Try and send, will except on BrokenPipeError if this connection
        r = sendMessage(obj)
        return (s, r)

    #connection closed, try to re-open
    except ConnectionError as e:
        print("Caught exception while attempting to connect: {}".format(e))
        return (None, -1)

# used to receive any one thing.
# this will timeout after t second if no message is received, and return None
# t = timeout in seconds
def recvWrap(s, t=1.0):
    liveSockets = []
    while True:
        readable, writeable, exceptional = select.select(liveSockets, [], liveSockets, t)
        if len(readable) == 0:
            return None

        for s in readable:
            # if getMessage returns None, then the socket was closed
            receipt = getMessage(s)
            for i in range(len(sockets)):
                if sockets[i] == s:
                    debugPrintP('Received', receipt, 'from id', i)
            if receipt is not None:
                return receipt
            else:
                liveSockets.remove(s)
                #update the sockets to the one that just died
                for i in range(len(sockets)):
                    if sockets[i] == s:
                        sockets[i] = None
