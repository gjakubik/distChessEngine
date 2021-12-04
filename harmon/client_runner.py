#!/usr/bin/env python

# imports
from re import L
import sys
import time
from stockfish import Stockfish
import game_client
import select
import socket
import json
import chess

# globals
DEPTH = 20 # num turns to sim (total, not each side)
ENGINE_TIME = 100 # milliseconds
ENCODING = 'utf8'


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
        mode = input(f'Would you like to play against the computer or play two engines against each other? (Enter user or cpu): ')
        cpuColor = input(f'Which color do you want the distributed AI to play with?: ')
        while cpuColor not in ["white", "black"]:
            cpuColor = input(f'Invalid input. What color do you want the distributed AI to play? (white or black): ')
        board_state = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        board = chess.Board(board_state) # this is the python-chess board
        client.stockfish.set_fen_position(board_state)
        board_state = client.stockfish.get_fen_position()
        print(board_state)
        while len(client.workers) < k:
            readable, writeable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is client.listener:
                    print("weee wooo weee wooo new connection alert!")
                    (sock, addr) = client.listener.accept()
                    inputs.append(sock)
                    client.workers.append(sock)
        
        print(client.stockfish.get_board_visual())
    while True:
        if role == 'master':
            offlineMaster(client, mode, board, cpuColor) # this does the stuff later in the while loop + in master_recv_server just for offline testing
            continue

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
                        master_recv_server(client, s)
                    elif s in client.workers: # received a move eval from a worker
                        master_recv_worker(client, s)

                elif role == 'worker':
                    # readable sockets could be: server sending an election message or master sending a move to evaluate or a new connection if a new master has been elected (???)
                    #if s is client.listener: # idk if this is how i wanna implement htis
                        #pass
                    if s is client.server: # some sort of election message
                        continue
                        
                    elif s is client.worker: # message from master, it's a move to evaluate (.worker is the socket which handles comm between worker and master)
                        worker_recv_master(client, s)
                        
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

# "offline" just means no frontend server
def offlineMaster(client, mode, board, cpuColor):
    # offline analog for master_recv_server(), it just prompts user for move input and takes board info that way instead of via socket communication
    color = 'white'
    if cpuColor == 'white':
        distCpuTurn(client, client.stockfish.get_fen_position(), board, cpuColor)
        color = 'black'
        print(client.stockfish.get_board_visual())

    if mode == 'user':
        # prompt user for move
        userMove = input('Please enter a move: ')
        if userMove == 'resign':
            print(f'===== GAME OVER ====== \n===== {cpuColor} WINS =====')
            exit()
        while not client.stockfish.is_move_correct(userMove):
            print(f'userMove is not valid. Moves must be of format: e2e4')
            userMove = input('Please enter a move: ')
        client.stockfish.make_moves_from_current_position([userMove])
        board.push(chess.Move.from_uci(userMove))
        if board.is_insufficient_material():
            print(f'====== DRAW: Insufficient Material =======')
            exit()
        if board.can_claim_threefold_repetition():
            print(f'====== DRAW: threefold repetition ======')
            exit()

        print(client.stockfish.get_board_visual())
    else: # in cpu mode, the the non distributed side is just playing with single node stockfish
        singleNodeMove = client.stockfish.get_best_move_time(1)
        if singleNodeMove == None:
            print(f'==== CHECKMATE ==== \n === {cpuColor} WINS! ===')
            exit()
        client.stockfish.make_moves_from_current_position([singleNodeMove])
        print(f'{"White" if cpuColor == "black" else "Black"} move is: {singleNodeMove}')
        board.push(chess.Move.from_uci(singleNodeMove))
        print(client.stockfish.get_board_visual())
    board_state = client.stockfish.get_fen_position()
    
    if cpuColor == 'black':
        distCpuTurn(client, board_state, board, cpuColor)
        print(client.stockfish.get_board_visual())

    # check for insuff material draw
    if board.is_insufficient_material():
            print(f'====== DRAW: Insufficient Material =======')
            exit()
    # check for threefold rep draw
    if board.can_claim_threefold_repetition():
        print(f'====== DRAW: threefold repetition =========')
        exit()

# code to decide move on distributed CPU's turn
def distCpuTurn(client, board_state, board, cpuColor):
    
    # generate k moves for computer, check that they are all valid
    move = ''
    moves = client.gen_moves()
    if len(moves) < 1:
        print(f'==== CHECKMATE ==== \n=== {"BLACK" if cpuColor == "white" else "WHITE"} WINS! ===')
        exit()
    evaluation = {}
    if len(client.workers) > 0:
        client.evals = []
        iter_list = zip(list(client.workers), list(moves))  # have to loop over copy of the lists bc we might need to remove from them during the loop if we detect failure
        for worker, move in iter_list:
            print(f'Sending {move}')
            response = client.assign_move(cpuColor, board_state, move, worker)
            if not response:
                print(f'Lost worker {client.workers.index(worker) + 1}' )
                client.workers.remove(worker)
                worker.close()
                client.k -= 1
                if len(moves) > 1: # try to remove the assigned move from the list, if it's the only one, we have to choose it 
                    moves.remove(move)
                else:
                    # if the move assigned to failed worker was last one in list, add it to client.evals 
                    # the rest of the logic SHOULD result in code skipping to bestMove assignment where this move is chosen by default
                    client.evals.append((move["Move"], {"cp": move["Centipawn"], "mate": move["Mate"]}))
                    break
        client.time_out = time.time() + 3 * DEPTH * ENGINE_TIME / 1000 # give workers 3 * the amount of time it takes to calc their eval to respond

        # wait for responses from the workers
        while len(client.evals) < len(client.workers):
            readable, writeable, exceptional = select.select(client.workers, client.workers, client.workers)
            for s in readable: # here we know that we can only get messages from a worker
                master_recv_worker(client, s)

            if time.time() > client.time_out:
                print("a client timed out!")
                # throw out the rest of the workers :( 
                iter_list = zip(client.workers, moves) # have to loop over copy of the lists bc we might need to remove from them during the loop if we detect failure
                for worker, move in iter_list:
                    if not any(move in e for e in client.evals): # if move has not been evaluated yet, throw out associated worker
                        client.workers.remove(worker)
                        worker.close()
                        print(f'Received no evaluation for move: {move}')
                        print(f'Closing worker {worker}')
                        client.k -= 1
                        if len(moves) > 1: # try to remove the assigned move from the list, if it's the only one, we have to choose it 
                            moves.remove(move)
                        else:
                            # if the move assigned to failed worker was last one in list, add it to client.evals 
                            # the rest of the logic SHOULD result in code skipping to bestMove assignment where this move is chosen by default
                            client.evals.append((move["Move"], {"cp": move["Centipawn"], "mate": move["Mate"]}))
                break

        # now we have responses from each worker --> time to choose best one 
        if len(client.evals) >= 1:
            bestMove = client.eval_responses(client.evals, cpuColor) 
            move = bestMove[0]
            evaluation = bestMove[1]
        else:
            bestMove = moves[0]
    else:
        # just use first move 
        bestMove = moves[0]
    if bestMove == None:
        print(moves)
    print(f'Distributed CPU ({cpuColor}) move is: {bestMove}')
    if evaluation != {}:
        print(f'Evaluation for move: {evaluation}')
    
    client.stockfish.make_moves_from_current_position([move['Move']])

    # make moves on Board object
    board.push(chess.Move.from_uci(move['Move']))

def master_recv_server(client, s):
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
        for worker, move in zip(client.workers, moves):
            response = client.assign_move(color, board_state, move, worker)
            if response == None:
                # TODO handle socket that returns none to this
                worker.close()
                client.workers.remove(worker)
                if len(client.workers) == 0:
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
        print(f'Message: {message}')
        response = client.server_send(client.game_server, message)
        if response == None:
            # TODO handle dead game server
            pass

def worker_recv_server(client, s):
    message = client.receive(s)
    try:
        type = message['type']
    except KeyError:
        print(f'Server sent unexpected JSON: {message}')
    if type == 'election':
        response = client.election_vote()
    elif type == 'election_result':
        #TODO make this client the master
        pass

def worker_recv_master(client, s):
    message = client.receive(s)
    try:
        type = message['type']
    except KeyError and TypeError:
        print(f'Master send bad formed JSON: {message}')
        # master failed -- need to trigger an election

    if type == 'move':
        color = message['color']
        board_state = message['board_state']
        move = message['move']

        # send acknowledgement response to master
        ack_message = json.dumps({"type": 'ack', 'status': 'OK', 'id': client.id})
        s.sendall(ack_message.encode(ENCODING))
        # evaluate the move and send the evaluation to the master
        eval_message = client.eval_move(board_state, move, DEPTH, ENGINE_TIME) # 99% sure this is the reason why we fail -- the master isn't currently responding to the eval moves and so it's throwing a typeError
        if not client.send(s, eval_message):
            # master failed -- need to trigger an election
            pass


def master_recv_worker(client, s):
    message = client.receive(s)
    try:
        type = message['type']
    except KeyError and TypeError:
        print(f'Worker sent bad JSON: {message}')
        client.workers.remove(s)
        s.close()
        return False
    
    if type == 'evaluation':
        move = message['move']
        eval = {"type": message["eval_type"], "value": message["eval_value"]}
        client.evals.append((move, eval)) # evals is list of (move, {type: cp|mate, value: value})
        # send ack to worker
        ack_message = json.dumps({'type': 'ack', 'owner': 'master', 'status': 'OK'})
        s.sendall(ack_message.encode(ENCODING))

        '''if len(client.evals == client.k):
            # we have all of our move evaluations and need to respond to the server
            move = client.eval_responses(client.evals, color)
            client.stockfish.make_moves_from_current_position([move])
            message = {'endpoint': '/move', 'state': client.stockfish.get_fen_position(), 'gameId': client.game_id, 'moveNum': move_num}
            print(move)
            message = json.loads(message)
            #client.server_send(client.server, message.encode(ENCODING)) # TODO capture response to this '''
    return True

if __name__ == '__main__':
    main()