#!/usr/bin/env python3

# imports
import sys
import socket
import json

# globals
NAME_SERVER = 'catalog.cse.nd.edu'
NS_PORT = 9097



def connect(host, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        client.connct((host, port))
    except ConnectionRefusedError:
        return None
    return client

def ns_connect(project):
    ns_sock = socket.socket(socket.AF_NET, socket.SOCK_STREAM)
    ns_sock.connect(NAME_SERVER, NS_PORT)
    # download service info
    req = f'GET /query.json HTTP/1.1\r\nHost:{NAME_SERVER}:{NS_PORT}\r\nAccept: application/json\r\n\r\n'
    ns_sock.sendall(req.encode())
    chunks = []
    while True:
        chunk = ns_sock.recv(1024)
        if not chunk or chunk == b'':
            break
        chunks.append(chunk)
    ns_sock.close()
    data = b''.join(chunks)
    data = data.decode()
    data = data.split('\n', 7) # in hw first 7 was all http header stuff, hopefully the same here ?
    json_data = json.loads(data)
    host, port = '', 0
    for el in json_data:
        if el['project'] == project:
            host = el['name']
            port = el['port']
            break
    return connect(host, port)

def usage():
    print("----- Game Client -----")
    print(f'Usage: ./game_client.py PROJECT NUM_MOVES')

def main():
    # take CLI args
    try: 
        project = sys.argv[1]
        num_moves = sys.argv[2]
    except IndexError:
        usage()
        exit(1)
    
    # connect to server
    client = ns_connect(project)
    if client == None:
        # TODO handle this error 
        pass
    pass

if __name__ == '__main__':
    main()