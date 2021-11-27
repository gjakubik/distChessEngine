#!/usr/bin/env python

# imports
import sys
import time
from stockfish import Stockfish
import game_client
import select
import json

# globals
DEPTH = 10 # num turns to sim
ENGINE_TIME = 3 # seconds

def main():
    # parse argv
    stockfish_path = sys.argv[1]
    project = sys.argv[2]
    owner = sys.argv[3]
    k = int(sys.argv[4])
    stockfish = Stockfish(stockfish_path)
    #"C:\\Users\\micha\Downloads\\stockfish_14.1_win_x64_avx2\\stockfish_14.1_win_x64_avx2\\stockfish_14.1_win_x64_avx2.exe"

    master_client = game_client.GameClient(project, owner, 'master', k, 0, stockfish)
    response = master_client.game_server_connect(project)
    engineId = json.loads(response.text)["engineId"]
    master_client.engine_id = engineId
    print(f'Engine ID: {master_client.engine_id}')

    master_client.last_update = master_client.update_ns()

    for i in range(k):
        worker = game_client.GameClient(project, owner, 'worker', k, i+1, stockfish)
        worker.game_server_connect(project) # open connection to server for each worker, only gets used if master fails
        worker.worker.connect((master_client.host, master_client.port))
        master_client.workers.append(worker)
        worker.engine_id = engieId
    
    inputs = [ worker.worker for worker in master_client.workers ] + [ master_client.listener ] 
    + [master_client.server] + [ worker.server for worker in master_client.workers ]
    # inputs: 
    #   worker sockets -- messages from worker to master
    #   worker.server -- messages from game server to worker
    #   master client listener -- new worker connections
    #   master_client.server -- messages from game server to master
    print(inputs)
    #outputs = [ worker.worker for worker in master_client.workers ]
    while True:
        try:
            # check for a new master
            for worker in master_client.workers:
                if worker.role == 'master':
                    master_client = worker
                    master_client.workers.remove(worker)
                    inputs = [worker.worker for worker in master_client.workers] + [master_client.listener] + [worker.server for worker in master_client.workers ] + [master_client.server]
                    #outputs = outputs = [ worker.worker for worker in master_client.workers ]
                    break

            # master checks for worker connections
            # master listens for message from name server and handles it if needed
            # TODO: in this block, have master client update the game server with current list of workers
            if (time.time() - master_client.last_update) >= 60:
                master_client.last_update = master_client.workers_update()
                master_client.last_update = master_client.update_ns(project)
            readable, writeable, exceptional = select.select(inputs, outputs, inputs)

            for s in readable: 
                if s is master_client.listener:
                    print('uh oh stinky uh oh stinky its connection time!')
                    (client, addr) = master_client.listener.accept()
                    inputs.append(client)
                elif s is any([worker.worker for worker in master_client.workers] + [master_client.server]): 
                    # handle receiving a message from the game server or one of the workers
                    message = master_client.receive(s)
                    try: 
                        messageOwner = message['owner']
                    except KeyError:
                        inputs.remove(s)
                        s.close()
                    # parse message
                    # TODO: maybe wanna make this split up a bit more 
                    if messageOwner == 'game_server':
                        print("*new york italian voice* ayyyy we got a game server over here!!!")
                        print(json.dumps(message))
                        if message['type'] == 'game_id':
                            master_client.game_id = message['game_id']
                            for worker in master_client.workers:
                                worker.game_id = message['game_id']
                        elif message['type'] == 'board_state':
                            # pick a move
                            board_state = message['board_state'] # fen string of the board state 
                            master_client.stockfish.set_fen_position(board_state)
                            moves = master_client.gen_moves() # generate moves
                            print(f'moves: {moves}')
                            # send messages to all the workers
                            if master_client.workers:
                                # assign moves
                                evals = [] # will be list of tuples of move and move's eval
                                for move in moves and worker in master_client.workers:
                                    response = master_client.assign_move(message['color'], message['board_state'], move, worker)
                                    if response['status'] != 'OK':
                                        # TODO handle failed client
                                    (move, evaluation) = worker.eval_move(message['board_state'], move, DEPTH, ENGINE_TIME)
                                    evals.append((move, evaluation)) 
                                # evaluate the worker responses
                                move = master_client.eval_responses(evals)[0] # [1] is the evaluation metric, may want it for stats 
                            else: # otherwise there's only the master, so we just use the best move from initial guess
                                move = moves[0]
                            # make move and respond to server
                            master_client.stockfish.make_moves_from_current_position([move])
                            message = {
                                'owner': 'master',
                                'engineId': master_client.engine_id,
                                'game_id': master_client.game_id,
                                'type': 'board_state',
                                'board_state': master_client.stockfish.get_fen_position()
                            }
                            print(f'Message: \n {message}')
                            response = master_client.send(master_client.game_server, message)
                            if response == None:
                                # TODO handle dead game server
                                pass
                    elif messageOwner == 'worker':
                        print("received message from a worker")
                        print(message)
                else: # s is a message from server --> worker
                    if s in [worker.worker for worker in master_client.workers()]:
                        for worker in master_client.workers:
                            if s == worker.worker:
                                break
                        # handle message from game server to worker -- election is happening
                        message = worker.receive(s)
                        print(message)
                        # receive message from the server 
                        # TODO handle malformed json
                        if message['type'] == 'election':
                            response = worker.election_vote()
                        elif message['type'] == 'election_result':
                            worker.make_master(master_client.workers)
                        else:
                            #TODO handle bad message from server to worker
                            pass

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