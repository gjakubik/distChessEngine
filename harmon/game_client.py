#!/usr/bin/env python

# imports
import sys
import select
import time
import socket
import json
from stockfish import Stockfish
import math


# globals
NAME_SERVER = 'catalog.cse.nd.edu'
NS_PORT = 9097
HEADER_SIZE = 64
GAME_SERVER = 'https://gavinjakubik.me:5050'
ENCODING = 'utf8'

class GameClient:
    def __init__(self, role, k, id, stockfish):
        self.role = role
        self.k = k
        self.id = id # this should increase from 0 - K
        self.stockfish = stockfish
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.server.connect(('gavinjakubik.me', 5050))

        if self.role == 'master':
            self.evals = []
            self.workers = [] # list of sockets
            # tcp listener to communicate with worker clients
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            listener.bind((socket.gethostname(), 0))
            hostname = socket.gethostname()
            self.host = socket.gethostbyname(hostname)
            self.port = listener.getsockname()[1]
            listener.listen(5)
            print(f'Listening on port: {self.port}')
            self.listener = listener # socket that will communicate with the workers
            
        else: 
            # TODO: make socket stuff for workers
            self.worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # worker socket 
            
        # other fields:
        # self.workers -- list of sockets connecting to the workers

    def workers_update(self):
        message = {
            'endpoint': f'/server/{self.engineId}',
            'host': self.host,
            'port': self.port,
            'role': self.role,
            'numWorkers': len(self.workers),
            'workers': self.workers
        }
        return self.server_send(message)

    def election_vote(self):
        # worker client votes in election to decide new master client
        # elections are bully algorithms where lowest id worker becomes new master
        message = {
            "type": "vote", 
            "id": self.id,
        }
        # TODO: handle timeouts
        response = self.server_send(self.server, message)
        return response

    def make_master(self, workers):
        # gets list of workers passed in from servere
        # make this worker client the new master 
        self.role = 'master'
        self.workers = workers

        # tcp listener to communicate with worker clients
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        listener.bind((socket.gethostname(), 0))
        hostname = socket.gethostname()
        self.host = socket.gethostbyname(hostname)
        self.port = listener.getsockname()[1]
        listener.listen(5)
        print(f'Listening on port: {self.port}')
        self.listener = listener # socket that will communicate with the workers
        
        # connect workers to new master
        for worker in self.workers:
            worker.worker.close()
            worker.worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            worker.worker.connect((self.host, self.port))
        
        # TODO: send message to all workers saying i am new master
    
    def handle_worker_fail():
        # have this master client handle the failure of one of the workers
        pass

    def eval_responses(self, evals, color):
        # TODO check the data structure of this stuff
        # evals is a list of (move, evaluation) tuples
        # returns a tuple of (move, evaluation)
        max_cp = (None, (-1) * math.inf)
        best_mate = (None, math.inf)
        for e in evals:
            if e[1][0] > max_cp[1]: 
                max_cp = (e[0], e[1][0])
            if math.abs(e[1][1]) < best_mate[1]:
                best_mate = (e[0], e[1][1])
        
        if math.abs(best_mate[1]) <= 3:
            return best_mate
        else:
            return max_cp

    def eval_move(self, board_state, move, depth, time):
        # TODO have stockfish play forward from the board state for some # of moves and report evaluation of it
        self.stockfish.set_fen_position(board_state)
        print(self.stockfish.get_board_visual())
        print(move)
        self.stockfish.make_moves_from_current_position(['d7d5'])
        print(self.stockfish.get_board_visual())
        for i in range(depth):
            next_move = self.stockfish.get_best_move_time(time)
            self.stockfish.make_moves_from_current_position([next_move])
            print(f'Move: {next_move}')
            if next_move == None:
                break
            print(self.stockfish.get_board_visual())
        evaluation = self.stockfish.get_evaluation()
        print(evaluation)
        message = {'type': 'evaluation', 'engineId': self.engineId, 'id': self.id, 'move': move, 'eval_type': evaluation['type'], 'eval_value': evaluation['value']}
        return self.send(self.worker, message)

    def gen_moves(self):
        num_moves = self.k if self.k > 1 else 1
        moves = self.stockfish.get_top_moves(num_moves)
        return moves

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
        response = self.send(worker, message)
        return response # either will be None or OK

    def server_send(self, client, message):
        # send message representing message length
        message = json.dumps(message)
        message = message.encode(ENCODING)
        client.sendall(message)

        # get the actual response
        response = self.receive(client)
        return response

    def send(self, client, message):
        # send message representing message length
        message = json.dumps(message)
        message = message.encode(ENCODING)
        len_message = str(len(message)).encode(ENCODING)
        len_message += b' '*(HEADER_SIZE - len(len_message))
        client.sendall(len_message)

        # send the actual message 
        client.sendall(message)

        # get the actual response
        response = self.receive(client)
        return response

    def receive(self, client):
        chunks = []
        bytes_rec = 0
        try: 
            message_len = client.recv(HEADER_SIZE)
        except ConnectionResetError:
            # TODO: handle this error
            print("connection was reset by server")
            return False
        try:
            message_len = int(message_len.decode(ENCODING))
        except ValueError:
            print("value error")
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
        message = {'type': f'chessEngine-{self.role}', 'owner': self.owner, 'port': self.port, 'project': self.project}
        message = json.dumps(message)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message.encode(ENCODING), (NAME_SERVER, NS_PORT))
        s.close()
        return time.time()

    