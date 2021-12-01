#!/usr/bin/env python

# imports
import sys
import socket
import time
from stockfish import Stockfish
import game_client
import select
import json

# globals
NAME_SERVER = 'catalog.cse.nd.edu'
NS_PORT = 9097
HEADER_SIZE = 64
GAME_SERVER = 'gavinjakubik.me'
GAME_SERVER_PORT = 5051
ENCODING = 'utf8'

def send(client, message):
    # send message representing message length
    print(message)
    message = json.dumps(message)
    message = message.encode(ENCODING)
    len_message = str(len(message)).encode(ENCODING)
    len_message += b' '*(HEADER_SIZE - len(len_message))
    print(len_message)
    client.sendall(len_message)

    # send the actual message 
    client.sendall(message)

    # get the actual response
    response = receive(client)
    return response

def receive(client):
    chunks = []
    bytes_rec = 0
    try: 
        message_len = client.recv(HEADER_SIZE)
    except ConnectionResetError:
        # TODO: handle this error
        print("connection was reset")
        return False
    try:
        message_len = int(message_len.decode(ENCODING))
    except ValueError:
        print(f'value error: {message_len}')
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

def main():
    stockfish_path = sys.argv[1]

    stockfish = Stockfish(stockfish_path)

    # create listener socket
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    listener.bind((socket.gethostname(), 0))
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    port = listener.getsockname()[1]
    listener.listen(5)
    print(f'Listening at: {host} {port}')

    # accept connection from master
    # while game running:
    #   receive master's move
    #   play master's move
    #   play own move
    #   send state to master
    
    # make first move
    move_num = 0
    move = stockfish.get_best_move()
    stockfish.make_moves_from_current_position([move])
    move_num += 1 
    # show curr board for fun + sanity check
    print(stockfish.get_board_visual())
    board_state = stockfish.get_fen_position()
    inputs = [listener]
    outputs = []
    while True:
        readable, writeable, exceptional = select.select(inputs, outputs, inputs)
        
        for s in readable:
            if s is listener: 
                # accept new connection
                (sock, addr) = listener.accept()
                print(f'Accepted new connection from: {addr}')
                inputs.append(sock)
                time.sleep(15)
                message = {
                        'state': stockfish.get_fen_position(),
                        'move_num': move_num,
                        'color':'black'
                    }
                send(sock, message)
                # for now, this is ONLY THE MASTER, nobody else talks to me 
            else:
                # message from the master
                message = receive(s)
                # parse message from master
                # will only ever be a move -- for now (muahahahah)
                try:
                    newBoardState = message['state']
                except KeyError and ValueError:
                    print(f'bad json message idk what that means {message}')
                
                stockfish.set_fen_position(newBoardState)
                move_num += 1
                print(stockfish.get_board_visual())
                next_move = stockfish.get_best_move()
                if next_move == 'None':
                    # we have a mate now
                    # TODO handle end of game
                    print(f'========== CHECKMATE ==========')
                    break
                else:
                    stockfish.make_moves_from_current_position([next_move])
                    move_num += 1 
                    print(stockfish.get_board_visual())
                    message = {
                        'state': stockfish.get_fen_position(),
                        'move_num': move_num,
                        'color':'black'
                    }
                    send(s, message)
        for s in writeable:
            pass
        for s in exceptional:
            pass
        pass



if __name__ == '__main__':
    main()