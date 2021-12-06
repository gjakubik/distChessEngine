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
        
        # tcp listener to communicate with worker clients
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        listener.bind((socket.gethostname(), 0))
        hostname = socket.gethostname()
        self.host = socket.gethostbyname(hostname)
        self.port = listener.getsockname()[1]
        self.listener = listener
        self.listener.listen(5)
        print(f'Listening on port: {self.port}')

        if self.role == 'master':
            self.evals = []
            self.workers = [] # list of sockets
            self.listener.listen(5)
            print(f'Listening on port: {self.port}')
        else: 
            # TODO: make socket stuff for workers
            self.worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn_master()

        self.last_update = self.update_ns()            
        
        # other fields:
        # self.workers -- list of sockets connecting to the workers

    def make_master(self, workers):
        self.role = 'master'
        self.k -= 1 # have to decrement this b/c we're losing a worker to gain a master
        self.worker.close()
        # initialize lists
        self.evals = []
        self.workers = [] # we dont have to append to this here b/c that gets done automatically when the workers try to connect to us 
        # tcp listener to communicate with worker clients
        # update the nameserver to let it know this is the new master
        self.last_update = self.update_ns()

    def eval_responses(self, evals, color):
        # evals is a list of (move, evaluation) tuples -- returns a tuple of (move, evaluation)
        
        print(evals)
        if color == 'white': 
            # positive is favorable (advantage white)
            max_cp = (None, (-1) * math.inf)
            best_mate = (None, math.inf)
            for e in evals: # e is tuple: (move, {cp|mate: value})
                moveEval = e[1]
                if moveEval['type'] == "cp":
                    if moveEval['value'] > max_cp[1]:
                        max_cp = (e[0], moveEval['value']) 
                elif moveEval['type'] == 'mate':
                    if moveEval['value'] < best_mate[1] and moveEval['value'] >= 0: # need to check that it's greater than 0, otherwise black mate in 3 would be marked as favorable!
                        best_mate = (e[0], moveEval['value'])
                    elif best_mate[1] <= 0: # the current best mate is a negative number (favors black) so we want to use vals w/ greater than it if > 0, less than it if < 0
                        if moveEval['value'] > best_mate[1] and moveEval['value'] >= 0: 
                            best_mate = (e[0], moveEval['value'])
                        elif moveEval['value'] < best_mate[1]:
                            best_mate = (e[0], moveEval['value'])
                    elif best_mate[1] == math.inf:
                        # always take this move's mate
                        best_mate = (e[0], moveEval['value'])
        else:
            # negative is favorable (advantage black)
            max_cp = (None, math.inf)
            best_mate = (None, (-1) * math.inf)
            for e in evals:
                moveEval = e[1]
                if moveEval['type'] == 'cp':
                    if moveEval['value'] < max_cp[1]: 
                        max_cp = (e[0], moveEval['value'])
                elif moveEval['type'] == 'mate':
                    if moveEval['value'] > best_mate[1] and moveEval['value'] <= 0: # need to check that it's less than 0, otherwise white mate in 3 would be marked as favorable!
                        best_mate = (e[0], moveEval['value'])
                    elif best_mate[1] >= 0: # current best mate is positive (favors white), so we wanna use vals w/ lesser value as long as they are less than 0, greater vals if they're > 0
                        if moveEval['value'] < best_mate[1] and moveEval['value'] <= 0:
                            best_mate = (e[0], moveEval['value'])
                        elif moveEval['value'] > best_mate[1]:
                            best_mate = (e[0], moveEval['value'])
                    elif best_mate[1] == (-1) * math.inf:
                        best_mate = (e[0], moveEval['value'])
        if abs(best_mate[1]) != math.inf: # if we got any moves w/ a mate, we use them 
            return best_mate
        else:
            return max_cp

    def eval_move(self, board_state, move, thinkingTime):
        #have stockfish play forward from the board state for some # of moves and report evaluation of it
        self.stockfish.set_fen_position(board_state)
        self.stockfish.make_moves_from_current_position([move['Move']])
        evalStart = time.time()
        while time.time() - evalStart < thinkingTime/1000:
            next_move = self.stockfish.get_best_move()
            if next_move == None: 
                break
            self.stockfish.make_moves_from_current_position([next_move])
        evaluation = self.stockfish.get_evaluation()
        message = {'type': 'evaluation','engineId': self.engineId, 'id': self.id, 'move': move, 'eval_type': evaluation['type'], 'eval_value': evaluation['value']}
        return message

    def gen_moves(self):
        num_moves = self.k if self.k > 1 else 1
        moves = self.stockfish.get_top_moves(num_moves)
        return moves

    def assign_move(self, color, board_state, move, worker, moveNum, mode='user', currGame=1, numGames=1):
        # move: representation of starting move assigned to this worker
        # worker: the socket the master has assigned to this worker
        # TODO: create & send message to WORKER telling them to evaluate MOVE
        # create json message
        message = {
            "type": "move",
            "color": color,
            "board_state": board_state,
            "move": move,
            "mode": mode,
            "currGame": currGame,
            "numGames": numGames,
            "moveNum": moveNum
        }
        response = self.send(worker, message)
        return response # either will be None or OK

    def server_send(self, client, message):
        message = json.dumps(message)
        message = message.encode(ENCODING)
        client.sendall(message)

        # get the actual response
        response = self.receive(client)
        print(response)
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
            if 'project' not in el.keys() or 'type' not in el.keys():
                continue
            if el['project'] == self.project:
                # see if it's a worker using regex 
                isWorker = bool(re.match('chessEngine-worker-([0-9]+)', el['type'])) 
                if isWorker:
                    # add the worker's id to the id list
                    id = el['type'].split('-', 2)[2] # if we split the type by -, the third element is the worker's id
                    workerIds.append(id)
                    # add the worker's address to the worker addrs list in case this guy becomes the master
                    workerAddrs.append((el['address'], el['port']))
        print(f'Worker IDs: {workerIds}')
        print(f'Worker Addrs: {workerAddrs}')
        if self.id == int(min(workerIds)):
            print('I am the master now')
            # make ourselves the master
            self.make_master(workerAddrs)
            # listen for workers
            print('Listening for new worker connecitons')
            while len(self.workers) < self.k:
                readable, writeable, exceptional = select.select([self.listener], [], [self.listener])
                for s in readable:
                    if s is self.listener:
                        print("weee wooo weee wooo new connection alert!")
                        (sock, addr) = self.listener.accept()
                        self.workers.append(sock)
        else:
            # connect to the new master
            masterId = min(workerIds)
            masterAddr = workerAddrs[workerIds.index(masterId)]
            print(f'Worker {masterId} is the new master. Connecting to: {masterAddr}')

            self.worker.close()
            self.worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            while True:
                try:
                    self.worker.connect(masterAddr)
                    break
                except ConnectionRefusedError:
                    workerIds.remove(masterId)
                    workerAddrs.remove(masterAddr)
                    masterId = min(workerIds)
                    masterAddr = workerAddrs[workerIds.index(masterId)]
                    if self.id == int(masterId):
                        while len(self.workers) < self.k:
                            readable, writeable, exceptional = select.select([self.listener], [], [self.listener])
                            for s in readable:
                                if s is self.listener:
                                    print("weee wooo weee wooo new connection alert!")
                                    (sock, addr) = self.listener.accept()
                                    self.workers.append(sock)
                        break

    def conn_master(self):
        nsData = self.connect_ns()
        for el in nsData:
            if 'project' not in el.keys() or 'type' not in el.keys() or 'lastheardfrom' not in el.keys():
                continue
            if el['project'] == self.project and bool(re.match('chessEngine-master', el['type'])) and el['lastheardfrom']:
                host = el['address']
                port = int(el['port'])
                self.worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.worker.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                print(host)
                print(port)
                self.worker.connect((host, port))