import React, { useRef, useState } from 'react';
import Chess from 'chess.js';
import { Chessboard } from 'react-chessboard';

import Box from '@mui/material/Box';
import Stack      from '@mui/material/Stack';
import Button     from '@mui/material/Button';
import TextField  from '@mui/material/TextField';
import Backdrop   from '@mui/material/Backdrop';
import Typography from '@mui/material/Typography';

export default function BoardView({ boardWidth }) {
    const chessboardRef                           = useRef();
    const [game, setGame]                         = useState(new Chess());
    const [arrows, setArrows]                     = useState([]);
    const [boardOrientation, setBoardOrientation] = useState('white');
    const [engineId, setEngineId]                 = useState("");
    const [username, setUsername]                 = useState("");
    const [gameEnd, setGameEnd]                   = useState(false);

    function safeGameMutate(modify) {
        setGame((g) => {
          const update = { ...g };
          modify(update);
          return update;
        });
      }
    
    function makeRandomMove() {
        const possibleMoves = game.moves();
    
        // exit if the game is over
        if (game.game_over() || game.in_draw() || possibleMoves.length === 0) {
            setGameEnd(true);
            return;
        }
    
        const randomIndex = Math.floor(Math.random() * possibleMoves.length);
        safeGameMutate((game) => {
            game.move(possibleMoves[randomIndex]);
        });
      }
    
    function onDrop(sourceSquare, targetSquare) {
        const gameCopy = { ...game };
        const move = gameCopy.move({
            from: sourceSquare,
            to: targetSquare,
            promotion: 'q' // always promote to a queen for example simplicity
        });
        setGame(gameCopy);
    
        // illegal move
        if (move === null) return false;
    
        setTimeout(makeRandomMove, 200);
        return true;
      }

    const resetHandler = () => {
        safeGameMutate((game) => {
            game.reset();
        });
        chessboardRef.current.clearPremoves();
    };

    const undoHandler = () => {
        safeGameMutate((game) => {
            game.undo();
        });
        chessboardRef.current.clearPremoves();
    };

    return (
        <React.Fragment>
            <Backdrop
                sx={{color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1}}
                open={gameEnd}
            >
                <Typography>Game Over</Typography>
            </Backdrop>
            <Stack sx={{alignItems: "center", marginTop: "40px"}} spacing={4}>
                <Stack direction="row" spacing={2}>
                    <TextField 
                        id="username" 
                        label="Username" 
                        variant="standard"
                        value={username}
                        onChange={(event) => {
                            setUsername(event.target.value);
                        }} 
                    />
                    <TextField 
                        id="engineId" 
                        label="EngineId" 
                        variant="standard"
                        value={engineId}
                        onChange={(event) => {
                            setEngineId(event.target.value);
                        }} 
                    />
                </Stack>
                <Chessboard
                    id="PlayVsPlay"
                    animationDuration={200}
                    boardOrientation={boardOrientation}
                    customArrows={arrows}
                    boardWidth={boardWidth}
                    position={game.fen()}
                    onPieceDrop={onDrop}
                    customBoardStyle={{
                        borderRadius: '4px',
                        boxShadow: '0 5px 15px rgba(0, 0, 0, 0.5)'
                    }}
                    ref={chessboardRef}
                />
                {gameEnd ? 
                (
                    <Stack direction="row" spacing={2}>
                        <Button variant="contained" onClick={resetHandler} disabled>
                            Reset
                        </Button>
                        <Button variant="contained" onClick={undoHandler} disabled>
                            Undo
                        </Button>
                    </Stack>
                )
                :
                (
                    <Stack direction="row" spacing={2}>
                        <Button variant="contained" onClick={resetHandler}>
                            Reset
                        </Button>
                        <Button variant="contained" onClick={undoHandler}>
                            Undo
                        </Button>
                    </Stack>
                )
                }
            </Stack>
        </React.Fragment>
    );
}