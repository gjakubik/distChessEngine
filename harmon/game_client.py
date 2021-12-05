#!/usr/bin/env python

# imports
import sys
import select
import time
import socket
import json
from stockfish import Stockfish
import math
import re


# globals
NAME_SERVER = 'catalog.cse.nd.edu'
NS_PORT = 9097
HEADER_SIZE = 64
GAME_SERVER = 'gavinjakubik.me'
GAME_SERVER_PORT = 5051
ENCODING = 'utf8'

class GameClient:
    def __init__(self, role, k, id, stockfish, owner, project):
        self.role = role
        self.k = k
        self.id = id # this should increase from 0 - K
        self.stockfish = stockfish
        self.owner = owner
        self.project = project
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((GAME_SERVER, GAME_SERVER_PORT))

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
            self.conn_master()

        self.last_update = self.update_ns()            
        
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

    def make_master(self, workers):
        self.role = 'master'

        self.worker.close()

        # initialize lists
        self.evals = []
        self.workers = [] # we dont have to append to this here b/c that gets done automatically when the workers try to connect to us 

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
        
        # update the nameserver to let it know this is the new master
        self.last_update = self.update_ns()

        # TODO send a message to the game server to inform it of the change

    def eval_responses(self, evals, color):
        # evals is a list of (move, evaluation) tuples -- returns a tuple of (move, evaluation)
        
        print(evals)
        if color == 'white': 
            # positive is favorable (advantage white)
            max_cp = (None, (-1) * math.inf)
            best_mate = (None, math.inf)
            for e in evals: # e is tuple: (move, {cp|mate: value})
                if e[1]['type'] == "cp":
                    if e[1]['value'] > max_cp[1]:
                        max_cp = (e[0], e[1]['value']) 
                elif e[1]['type'] == 'mate':
                    if e[1]['value'] < best_mate[1] and e[1]['value'] >= 0: # need to check that it's greater than 0, otherwise black mate in 3 would be marked as favorable!
                        best_mate = (e[0], e[1]['value'])
        else:
            # negative is favorable (advantage black)
            max_cp = (None, math.inf)
            best_mate = (None, (-1) * math.inf)
            for e in evals:
                if e[1]['type'] == 'cp':
                    if e[1]['value'] < max_cp[1]: 
                        max_cp = (e[0], e[1]['value'])
                elif e[1]['type'] == 'mate':
                    if e[1]['value'] > best_mate[1] and e[1]['value'] <= 0: # need to check that it's less than 0, otherwise white mate in 3 would be marked as favorable!
                        best_mate = (e[0], e[1]['value'])
        if abs(best_mate[1]) != math.inf: # if we got any moves w/ a mate, we use them 
            return best_mate
        else:
            # print out the cp values of given moves
            for e in evals:
                print(e[1]['value'])
            return max_cp

    def eval_move(self, board_state, move, depth, time):
        #have stockfish play forward from the board state for some # of moves and report evaluation of it

        self.stockfish.set_fen_position(board_state)
        print(move)
        self.stockfish.make_moves_from_current_position([move['Move']])
        for i in range(depth):
            next_move = self.stockfish.get_best_move_time(time)
            if next_move == None: 
                break
            self.stockfish.make_moves_from_current_position([next_move])
            print(f'Move: {next_move}')
        evaluation = self.stockfish.get_evaluation()
        message = {'type': 'evaluation','engineId': self.engineId, 'id': self.id, 'move': move, 'eval_type': evaluation['type'], 'eval_value': evaluation['value']}
        return message

    def gen_moves(self):
        num_moves = self.k if self.k > 1 else 1
        moves = self.stockfish.get_top_moves(num_moves)
        return moves

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
        response = client.recv(HEADER_SIZE)
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
            print(message_len)
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
        # update the name server with this client's info
        # role and id are stored in type so that we can super easily figure out winner of elections
        message = {'type': f'chessEngine-{self.role}-{self.id}', 'owner': self.owner, 'port': self.port, 'project': self.project}
        message = json.dumps(message)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message.encode(ENCODING), (NAME_SERVER, NS_PORT))
        s.close()
        return time.time()

    def connect_ns(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((NAME_SERVER, 9097))
        # download service info JSON
        req = 'GET /query.json HTTP/1.1\r\nHost:catalog.cse.nd.edu:9097\r\nAccept: application/json\r\n\r\n'
        s.sendall(req.encode(ENCODING))
        # get info back from name server
        chunks = []
        while True:
            chunk = s.recv(1024)
            if not chunk or chunk == b'': # ns failed to send info
                break
            chunks.append(chunk)
        s.close()
        data = b''.join(chunks)
        data = data.decode()
        data = data.split('\n', 7)[-1] # first 7 lines are http header stuff -- not recognizeable by json
        json_data = json.loads(data)
        return json_data # returns the name server's info as a json
    
    def handle_election(self):
        # get name server data
        # parse name server for all chessEngine entries assoc. with this project, pull the ids from all entries with worker types
        # compare pulled id to own id, if own is smaller than the rest, we are master
        nsData = self.connect_ns()
        workerIds = []
        workerAddrs = []
        for el in nsData:
            if el['project'] == self.project:
                # see if it's a worker using regex 
                isWorker = bool(re.match('chessEngine-worker-([0-9]+)', el['type'])) 
                if isWorker and el['lastheardfrom']:
                    # add the worker's id to the id list
                    id = el['type'].split('-', 2)[2] # if we split the type by -, the third element is the worker's id
                    workerIds.append(id)
                    # add the worker's address to the worker addrs list in case this guy becomes the master
                    workerAddrs.append((el['address'], el['port']))
        if self.id == min(workerIds):
            # make ourselves the master
            self.make_master(workerAddrs)
        else:
            # TODO: connect ot the new master
            pass

    def conn_master(self):
        nsData = self.connect_ns()
        for el in nsData:
            if el['project'] == self.project and bool(re.match('chessEngine-master')) and el['lastheardfrom']:
                host = el['address']
                port = el['port']
                self.worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.worker.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.worker.connect((host, port))