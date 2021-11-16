#!/usr/bin/env python3

# imports
import sys
import select
import time
import socket
import requests
import http
import json
from stockfish import Stockfish


# globals
NAME_SERVER = 'catalog.cse.nd.edu'
NS_PORT = 9097
HEADER_SIZE = 32

class GameClient:
    def __init__(self, project, owner, role, k, id, stockfish):
        self.project = project
        self.role = role
        self.owner = owner
        self.k = k
        self.id = id # this should increase from 0 - K
        self.stockfish = stockfish

        if self.role == 'master':
            # establish HTTP server for communication with the engine client
            Handler = http.server.SimpleHTTPRequestHandler
            self.server = http.server.HTTPServer(("", 8000), Handler)

            # tcp listener to communicate with worker clients
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            listener.bind((socket.gethostname(), 0))
            self.port = listener.getsockname()[1]
            listener.listen(5)
            print(f'Listening on port: {self.port}')
            self.listener = listener # socket that will communicate with the workers

            self.sender = self.ns_game_server_connect(project) # socket that will send messages to the server
        else: 
            # TODO: make socket stuff for workers
            self.worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # worker socket 
            
        # other fields:
        # self.workers -- list of sockets connecting to the workers
        # self.master -- socket connecting to the master client
        return self

    def eval_move(self, board_state, depth, time):
        # TODO have stockfish play forward from the board state for some # of moves and report evaluation of it
        worker_fish = Stockfish()
        worker_fish.set_fen_position(board_state)
        for i in range(depth):
            move = worker_fish.get_best_move_time(time)
            if move == None:
                break
            worker_fish.make_moves_from_current_position([move])
            move = worker_fish.get_best_move_time(time)
            if move == None:
                break
            worker_fish.make_moves_from_current_position([move])
        return worker_fish.get_evaluation() # this is a dict of eval in CP or mate in x 

    def gen_moves(self):
        moves = self.stockfish.get_top_moves(self.k)
        return moves

    def get_master_move(self, board_state):
        # 1. master node picks K most optimal moves
        moves = self.gen_moves(self.k, board_state)
        # 2. master node assigns work to each worker
        for index, worker in enumerate(self.workers):
            if self.assign_move(moves[index], worker) == None:
                # TODO: handle bad worker reponse
                pass
        # 3. master waits on workers to send messages
        ratings = self.get_worker_responses()
        # 4. master picks most optimal move
        move = self.pick_optimal(ratings)
        # 5. master sends its move to the game server
        self.stockfish.make_moves_from_current_position(move)
        message = {
            "type": "board_state",
            "board_state": self.stockfish.get_fen_position()
        }
        return self.send(self.game_server, message)

    def get_worker_responses(self):
        # TODO: select between the workers to read back their responses 
        # return list of tuples with move and rating 
        pass

    def assign_move(self, color, board_state, move, worker):
        # move: representation of starting move assigned to this worker
        # worker: the socket the master has assigned to this worker
        # TODO: create & send message to WORKER telling them to evaluate MOVE
        # create json message
        message = {
            "type": "move",
            "color": color,
            "board_state": board_state,
            "move": move
        }
        response = self.send(message, worker)
        return response # either will be None or OK

    def send(self, client, message):
        # send message representing message length
        message = json.dumps(message)
        message = message.encode()
        len_message = str(len(message)).encode()
        len_message += b' '*(HEADER_SIZE - len(len_message))
        client.sendall(len_message)

        # send the actual message 
        client.sendall(message)

        # capture the response length message
        res_len = client.recv(HEADER_SIZE) # binary object
        res_len = res_len.decode()
        if res_len == '':
            # server didn't send us an appropriate response
            return None 
        res_len = int(res_len)
        # get the actual response
        response = self.receive(client, res_len)
        return response

    def receive(self, client):
        chunks = []
        bytes_rec = 0
        try: 
            message_len = client.recv(HEADER_SIZE)
        except ConnectionResetError:
            # TODO: handle this error
            return False
        try:
            message_len = int(message_len.decode())
        except ValueError:
            return False
        
        while bytes_rec < message_len:
            chunk = client.recv(message_len - bytes_rec)
            if chunk == b'': # bad response
                return None
            bytes_rec += len(chunk)
            chunks.append(chunk)
        chunks = b''.join(chunks)
        message = json.loads(chunks)
        return message

    # returns a socket connected to the specified host and port
    def connect(host, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            client.connect((host, port))
        except ConnectionRefusedError:
            return None
        return client

    def update_ns(self):
        message = {'type': f'chessEngine-{self.role}', 'owner': {self.owner}, 'port': port, 'project': self.project}
        message = json.dumps(message)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGAM)
        s.sendto(message.encode(), (NAME_SERVER, NS_PORT))
        s.close()
        return time.time()
    
    # establish a connection with the game server via nameserver
    def ns_game_server_connect(self, project):
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
        host, port, recent = '', 0, 0
        for el in json_data:
            if el['project'] == project and el['type'] == 'chessEngine-gameServer':
                # connect the game server
                if el['lastheardfrom'] > recent: 
                    host = el['name']
                    port = el['port']
                    recent = el['lastheardfrom']
                break
        self.game_server = self.connect(host, port) # TODO: do we wanna update this every time we call connect? 

    def ns_worker_connect(self, project):
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
            if el['project'] == project and el['type'] == 'chessEngine-worker':
                # create a socket for the worker, add it to workers list
                host = el['name']
                port = el['port']
                self.workers.append(self.connect(host, port))
    
    def ns_master_connect(self, project):
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
        host, port, recent = '', 0, 0
        for el in json_data:
            if el['project'] == project and el['type'] == 'chessEngine-worker':
                # create a socket for the master, save it as self.master
                if el['lastheardfrom'] > recent:
                    host = el['name']
                    port = el['port']
                    recent = el['lastheardfrom']
                break
        self.master = self.connect(host, port)

def main():
    # TODO: split this off into a diff file
    stockfish = Stockfish(parameters={"Threads": 1, "Minimum Thinking Time": 30})

    # TODO parse argv
    project, owner, k, = '', '',  0

    master_client = GameClient(project, 'master', k, 0, stockfish)
    master_client.ns_game_server_connect(project)

    master_client.last_update = master_client.update_ns()
    
    inputs = master_client.workers + [ master_client.listener ]
    outputs = [ ]
    while True:
        try:
            # master checks for worker connections
            # master listens for message from game server and handles it if needed
            if (time.time() - master_client.last_update) >= 60:
                master_client.last_update = master_client.update_ns(project)
            readable, writeable, exceptional = select.select(inputs, outputs, inputs)

            for s in readable: 
                if s is master_client.listener:
                    (client, addr) = master_client.listener.accept()
                    inputs.append(client)
                    master_client.workers.append(client)
                else: 
                    # one of the workers sent master a message
                    message = master_client.receive(s)
                    # parse the message
                    try:
                        messageType = message['type']
                    except KeyError:
                        result = json.dumps({'status': 'invalid', 'message': 'Worker sent bad JSON'})
                        print(result)
                        inputs.remove(s)
                        master_client.workers.remove(s)
                        s.close()
                        continue
                    if messageType == 'board_state':
                        # accept worker board state message
                        pass
                    # TODO: figure out the other message types 
                    pass
            for s in exceptional:
                inputs.remove(s)
                master_client.workers.remove(s)
                s.close()

        except KeyboardInterrupt:
            for s in inputs:
                s.close()
            return


if __name__ == '__main__':
    main()