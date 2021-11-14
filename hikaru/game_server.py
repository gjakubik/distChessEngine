#!/usr/bin/env pyhton3

# imports
import sys
import socket
import json
import time 
import select

# globals
NAME_SERVER = 'catalog.cse.nd.edu'
NS_PORT = 9097 # i think socket expects this to be separate from url and be an int
NS_PERIOD = 60 # update name server every 60 seconds

# ------ Define the Server --------

def send(s):
    # TODO: send message to game client/gui client 
    pass

def receive(s):
    # TODO: receive a message from a game client OR gui client socket
    pass

def update_ns(port, project, owner):
    # send UDP message to name server
    # {type: ???, owner: OWNER port: PORT, project: PROJECT}
    message = json.dumps({'type': 'chessEngine', 'owner': owner, 'port': port, 'project': project}) #TODO figure out what 'type' should be
    ns_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ns_sock.sendto(message.encode(), (NAME_SERVER, NS_PORT))
    ns_sock.close()
    return time.time() 


def usage():
    # TODO create a usage message to display to user when they do sm wrong
    print("------- game_server.py -------")
    print("Usage: ./game_server.py PROJECT_NAME OWNER")

def main():
    # capture command line options
    # TODO figure out what else we wanna get from command line 
    # for now, just starting with project name 
    try:
        project = sys.argv[1]
        owner = sys.argv[2]
    except IndexError:
        usage()
        exit(1)
    
    # start server socket and listen for connections
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((socket.gethostname(), 0)) # listen on any port
    port = server.gethostname()[1]
    server.listen(5)
    print(f'Listening on port {port}')

    # update name server 
    last_update = update_ns(port, project, owner)
    inputs = [ server ] # sockets we'll read from
    outputs = [ ] # sockets we'll write to

     # listening loop
    while inputs:
        try:
            # periodically update name server
            if(time.time() - last_update >= NS_PERIOD):
                last_update = update_ns(port, project)
            
            readable, writable, exceptional = select.select(inputs, outputs, inputs)

            # handle readable sockets
            for s in readable:
                if s is server: # we have new incoming connection
                    (client, addr) = server.accept()
                    print(f'accepted connection from {addr[0]}:{addr[1]}')
                    inputs.append(client)
                    continue
                clientJson = receive(s)
                if not clientJson:
                    print(f'Closing {s.getpeername()} -- received no data')
                    inputs.remove(s)
                    s.close()
                    continue
                
                # TODO: parse json message from gui client and/or game client

            # TODO: handle writeable sockets

            # close exceptional sockets
            for s in exceptional:
                inputs.remove(s)
                s.close()
        except KeyboardInterrupt:
            print("Shutting down server... goodbye")
            for s in inputs:
                s.close()
            return

if __name__ == '__main__':
    main()