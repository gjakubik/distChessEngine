#!/usr/bin/env python

# imports
import sys
import time
from stockfish import Stockfish
import game_client
import select
import json


def main():
    stockfish = Stockfish(sys.argv[1]) # need to pass in the path to the stockfish executable as first command line argument
    
    # TODO parse argv
    project = sys.argv[2]
    owner = sys.argv[3]
    k = int(sys.argv[4])

    master_client = game_client.GameClient(project, owner, 'master', k, 0, stockfish)
    response = master_client.game_server_connect(project)
    master_client.engine_id = json.loads(response.text)["engineId"]
    print(f'Engine ID: {master_client.engine_id}')

    master_client.last_update = master_client.update_ns()

    for i in range(k):
        worker = game_client.GameClient(project, owner, 'worker', k, i+1, stockfish)
        master_client.workers.append(worker)
    
    
    inputs = [ worker.worker for worker in master_client.workers ] + [ master_client.listener ]
    print(inputs)
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
                    print('uh oh stinky uh oh stinky its connection time!')
                    (client, addr) = master_client.listener.accept()
                    inputs.append(client)
                else:
                    # handle receiving a message from the game server or one of the workers
                    message = master_client.receive(s)
                    try: 
                        messageOwner = message['owner']
                    except KeyError:
                        inputs.remove(s)
                        s.close()
                    # TODO: parse message
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
                            moves = master_client.gen_moves()
                            print(f'moves: {moves}')
                            # send messages to all the workers
                            if master_client.workers:
                                # TODO handle the workers
                                pass
                            else: # otherwise there's only the master, so we just use the best move from initial guess
                                move = moves[0]
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
            for s in exceptional:
                inputs.remove(s)
                s.close()

        except KeyboardInterrupt:
            for s in inputs:
                s.close()
            exit()


if __name__ == '__main__':
    main()