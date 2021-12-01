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
    if role == 'master':
        try:
            #engineId = sys.argv[5]
            test_host = sys.argv[5]
            test_port = int(sys.argv[6])
        except IndexError:
            print('no host/port given')
    else:
        try:
            #engineId = sys.argv[5]
            master_host = sys.argv[5]
            master_port = int(sys.argv[6])
        except IndexError:
            print('no host/port given')


    stockfish = Stockfish(stockfish_path, parameters={'Minimum Thinking Time': 1})
    #"C:\\Users\\micha\Downloads\\stockfish_14.1_win_x64_avx2\\stockfish_14.1_win_x64_avx2\\stockfish_14.1_win_x64_avx2.exe"

   
    
    if role == "master":
        client = game_client.GameClient(role, k, id, stockfish, test_host, test_port)
        print(f'Host: {client.host}  Port: {client.port}')
        '''# get engine id from server
        message = {
            'method': 'POST',
            'endpoint': '/server', 
            'role': 'master', 
            'host': client.host, 
            'port': client.port, 
            'numWorkers': k
        }
        response = client.server_send(client.server, message)
        try:
            client.engineId = response['engineId']
            print(f'Registered the engine. Engine ID: {client.engineId}')
        except KeyError:
            print(f'ERROR: Unexpected json formatting from server: {response}')'''
        inputs = [client.listener] + [client.server] + client.workers
        outputs = []

    elif role == "worker":
        client = game_client.GameClient(role, k, id, stockfish, master_host, master_port)
        '''# master address from server
        client.engineId = engineId 
        message = {
            'method': 'GET',
            'endpoint': f'/server/{client.engineId}', 
            'role': 'worker', 
            'engineId': client.engineId,
            'id': id # this is NOT a gameID
        }
        response = client.server_send(client.server, message)
        try:
            master_host = response['host']
            master_port = response['port']
        except KeyError:
            print(f'Server sent unexpected JSON: {response}')
        client.engineId = engineId '''
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

            # TODO: in this block, have master client update the game server with current list of workers
            '''if time.time() - last_update > 60:
                response = client.workers_update()
                # TODO: error check 
                last_update = time.time()'''

            readable, writeable, exceptional = select.select(inputs, outputs, inputs)

            for s in readable: 
                if role == 'master':
                    # readable sockets could be: server sending game state or worker sending a move evaluation or listener accepting a new connection
                    if s is client.listener:
                        (sock, addr) = client.listener.accept()
                        print(f'Accepted a new connection from: {addr}')
                        inputs.append(sock)
                        client.workers.append(sock)
                    elif s is client.server: # received message from server -- it's engine's turn to make a move
                        message = client.receive(s)
                        try:
                            #gameId = message['gameId']
                            board_state = message['state']
                            move_num = message['moveNum']
                            color = message['color']
                        except KeyError:
                            print(f'Server sent bad JSON: {message}')
                        move_start = time.time()
                        #client.gameId = gameId
                        client.stockfish.set_fen_position(board_state)
                        moves = client.gen_moves()
                        if client.workers:
                            client.evals = []
                            for worker, move in zip(client.workers, moves):
                                response = client.assign_move(color, board_state, move, worker)
                                if response == None:
                                   # TODO handle socket that returns none to this
                                    pass
                        else: # just pick the first move b/c we don't have any workers 
                            move = moves[0]
                            # make move and respond to server
                            client.stockfish.make_moves_from_current_position([move])
                            message = {
                                'method': 'POST',
                                'endpoint': '/move',
                                #'engineId': client.engineId,
                                #'gameId': client.gameId,
                                'state': client.stockfish.get_fen_position(),
                                'moveNum': int(move_num) + 1
                            }
                            response = client.server_send(client.server, message)
                            print(f'Move {move_num} total time: {total_move_time}')
                            print(f'Move {move_num} evaluation: {evaluation[1]}')
                            if response == None:
                                # TODO handle dead game server
                                pass
                    elif s in client.workers: # received a move eval from a worker
                        message = client.receive(s)
                        try:
                            move = message['move']
                            evaluation = message['evaluation']
                            client.evals.append((move, evaluation))
                        except KeyError and TypeError:
                            print(f'Worker sent bad JSON: {message}')
                            client.evals.append((None, None))
                            continue
                        if len(client.evals == k):
                            # we have all of our move evaluations and need to respond to the server
                            evaluation = client.eval_responses(client.evals, color)
                            move = evaluation[0]
                            client.stockfish.make_moves_from_current_position([move])
                            message = {
                                'method': 'POST', 
                                'endpoint': '/move', 
                                'state': client.stockfish.get_fen_position(), 
                                #'engineId': client.engineId, 
                                #'gameId': client.gameId, 
                                'moveNum': int(move_num) + 1
                            }
                            response = client.server_send(client.server, message)
                            total_move_time = time.time() - move_start
                            print(f'Move {move_num} total time: {total_move_time}')
                            print(f'Move {move_num} evaluation: {evaluation[1]}')
                elif role == 'worker':
                    # readable sockets could be: server sending an election message or master sending a move to evaluate or a new connection if a new master has been elected (???)
                    #if s is client.listener: # idk if this is how i wanna implement htis
                        #pass
                    '''if s is client.server: # some sort of election message
                        message = client.receive(s)
                        print(f'Message from server to worker: {message}')
                        continue
                        try:
                            type = message['type']
                        except KeyError:
                            print(f'Server sent unexpected JSON: {message}')
                        if type == 'election':
                            response = client.election_vote
                        elif type == 'election_result':
                            #TODO make this client the master
                            pass'''
                    #elif s is client.worker: # message from master, it's a move to evaluate (.worker is the socket which handles comm between worker and master)
                    message = client.receive(s)
                    try:
                        #gameId = message['gameId']
                        color = message['color']
                        board_state = message['state']
                        move = message['move']
                    except KeyError and TypeError:
                        print(f'Master sent bad formed JSON: {message}')
                    '''if gameId:
                        client.gameId = gameId
                    else:
                        print(f'No gameID, this is a problem')
                        continue'''
                    response = client.eval_move(board_state, move, DEPTH, ENGINE_TIME)
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