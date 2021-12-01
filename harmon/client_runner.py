#!/usr/bin/env python

# imports
import sys
import time
from stockfish import Stockfish
import game_client
import select
import json

# globals
DEPTH = 20 # num turns to sim (total, not each side)
ENGINE_TIME = 500 # milliseconds

def main():
    # parse argv
    stockfish_path = sys.argv[1]
    role = sys.argv[2] # master or worker
    id = int(sys.argv[3])
    k = int(sys.argv[4])
    try:
        engineId = sys.argv[5]
    except IndexError:
        print('no engine id given, this is ok if you\'re starting a master')
    try:
        master_host = sys.argv[6]
        master_port = int(sys.argv[7])
    except IndexError:
        print('no host or port given, ok if ur starting master')

    stockfish = Stockfish(stockfish_path, parameters={'Minimum Thinking Time': 1})
    #"C:\\Users\\micha\Downloads\\stockfish_14.1_win_x64_avx2\\stockfish_14.1_win_x64_avx2\\stockfish_14.1_win_x64_avx2.exe"

    client = game_client.GameClient(role, k, id, stockfish)
    client.engineId = engineId 
    
    if role == "master":
        print(f'Host: {client.host}  Port: {client.port}')
        # get engine id from server
        '''message = {'endpoint': '/server', 'role': 'master', 'host': client.host, 'port': client.port, 'numWorkers': k}
        response = client.server_send(client.server, message)
        try:
            client.engineId = response['serverId']
            print(f'Registered the engine. Engine ID: {client.engineId}')
        except KeyError:
            print(f'ERROR: Unexpected json formatting from server: {response}')'''
        inputs = [client.listener] + [client.server] + client.workers
        outputs = []

    elif role == "worker":
        # master address from server
        '''client.engineId = engineId 
        message = {'endpoint': '/server', 'role': 'worker', 'engineId': client.engineId, 'id': id}
        response = client.server_send(client.server, message)
        try:
            master_host = response['host']
            master_port = response['port']
            client.worker.connect((master_host, master_port))
        except KeyError:
            print(f'Server sent unexpected JSON: {response}')'''
        client.worker.connect((master_host, master_port))
        inputs = [client.server] + [client.worker] 
        outputs = []
    # inputs: 
    #   worker sockets -- messages from worker to master
    #   worker.server -- messages from game server to worker
    #   master client listener -- new worker connections
    #   master_client.server -- messages from game server to master

    print(inputs)
    #outputs = [ worker.worker for worker in master_client.workers ]
    last_update = time.time()
    if role == 'master':
        board_state = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        color = 'black'
        client.stockfish.set_fen_position(board_state)
        client.stockfish.make_moves_from_current_position(['e2e4'])
        board_state = client.stockfish.get_fen_position()
        print(board_state)
        moves = client.gen_moves()
        print(moves)
        time.sleep(30)
        while len(client.workers) < k:
            readable, writeable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is client.listener:
                    print("weee wooo weee wooo new connection alert!")
                    (sock, addr) = client.listener.accept()
                    inputs.append(sock)
                    client.workers.append(sock)

        if client.workers:
            client.evals = []
            client.worker_timestart = time.time()
            for worker, move in zip(client.workers, moves):
                response = client.assign_move(color, board_state, move, worker)
                print(response)
                if response == None:
                    # TODO handle socket that returns none to this
                    pass
    while True:
        try:
            # check for a new master -- TODO fix this to reflect distribution
            '''for worker in master_client.workers:
                if worker.role == 'master':
                    master_client = worker
                    master_client.workers.remove(worker)
                    inputs = [worker.worker for worker in master_client.workers] + [master_client.listener] + [worker.server for worker in master_client.workers ] + [master_client.server]
                    #outputs = outputs = [ worker.worker for worker in master_client.workers ]
                    break'''

            '''# TODO: in this block, have master client update the game server with current list of workers
            if time.time() - last_update > 60:
                response = client.worker_update()
                # TODO: error check 
                last_update = time.time()'''

            readable, writeable, exceptional = select.select(inputs, outputs, inputs)

            for s in readable: 
                if role == 'master':
                    # readable sockets could be: server sending game state or worker sending a move evaluation or listener accepting a new connection
                    if s is client.listener:
                        print("weee wooo weee wooo new connection alert!")
                        (sock, addr) = client.listener.accept()
                        inputs.append(sock)
                        client.workers.append(sock)
                    elif s is client.server: # received message from server -- it's engine's turn to make a move
                        message = client.receive(s)
                        try:
                            board_state = message['state']
                            move_num = message['moveNum']
                            color = message['color']
                        except KeyError:
                            print(f'Server sent bad JSON: {message}')
                        client.stockfish.set_fen_position(board_state)
                        moves = client.gen_moves()
                        if client.workers:
                            client.evals = []
                            for worker in client.workers and move in moves:
                                client.stockfish.set_fen_position(board_state)
                                client.stockfish.make_moves_from_current_position([move])
                                new_board_state = client.stockfish.get_fen_position()
                                response = client.assign_move(color, new_board_state, move, worker)
                                if response == None:
                                   # TODO handle socket that returns none to this
                                    pass
                        else: # just pick the first move b/c we don't have any workers 
                            move = moves[0]
                            # make move and respond to server
                            client.stockfish.make_moves_from_current_position([move])
                            message = {
                                'endpont': '/move',
                                'engineId': client.engineId,
                                'state': client.stockfish.get_fen_position(),
                                'moveNum': move_num
                            }
                            print(f'Message: \n {message}')
                            response = client.send(client.game_server, message)
                            if response == None:
                                # TODO handle dead game server
                                pass
                    elif s in client.workers: # received a move eval from a worker
                        message = client.receive(s)
                        try:
                            move = message['move']
                            evaluation = message['evaluation']
                            client.evals.append((move, evaluation))
                        except KeyError:
                            print(f'Worker sent bad JSON: {message}')
                            client.workers.remove(s)
                            s.close()
                            client.evals.append((None, None))
                        if len(client.evals == k):
                            # we have all of our move evaluations and need to respond to the server
                            move = client.eval_responses(client.evals, color)
                            client.stockfish.make_moves_from_current_position([move])
                            message = {'endpoint': '/move', 'state': client.stockfish.get_fen_position(), 'gameId': client.game_id, 'moveNum': move_num}
                elif role == 'worker':
                    # readable sockets could be: server sending an election message or master sending a move to evaluate or a new connection if a new master has been elected (???)
                    #if s is client.listener: # idk if this is how i wanna implement htis
                        #pass
                    if s is client.server: # some sort of election message
                        continue
                        message = client.receive(s)
                        try:
                            type = message['type']
                        except KeyError:
                            print(f'Server sent unexpected JSON: {message}')
                        if type == 'election':
                            response = client.election_vote
                        elif type == 'election_result':
                            #TODO make this client the master
                            pass
                    elif s is client.worker: # message from master, it's a move to evaluate (.worker is the socket which handles comm between worker and master)
                        message = client.receive(s)
                        try:
                            color = message['color']
                            board_state = message['board_state']
                            move = message['move']
                        except KeyError and TypeError:
                            print(f'Master sent bad formed JSON: {message}')
                        response = client.eval_move(board_state, move, DEPTH, ENGINE_TIME) # 99% sure this is the reason why we fail -- the master isn't currently responding to the eval moves and so it's throwing a typeError
                        # TODO: error check this response 
            for s in writeable: 
                pass

            for s in exceptional:
                inputs.remove(s)
                s.close()
            outputs = []
        except KeyboardInterrupt:
                for s in inputs:
                    s.close()
                exit()


if __name__ == '__main__':
    main()