import React, { useRef, useState } from 'react';
import Chess from 'chess.js';
import { Chessboard } from 'react-chessboard';
import makeMove from '../../services/makeMove';
import startGame from '../../services/startGame';

import Box from '@mui/material/Box';
import Stack      from '@mui/material/Stack';
import Button     from '@mui/material/Button';
import TextField  from '@mui/material/TextField';
import Backdrop   from '@mui/material/Backdrop';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';

export default function BoardView({ boardWidth }) {
    const chessboardRef                           = useRef();
    const [game, setGame]                         = useState(new Chess());
    const [arrows, setArrows]                     = useState([]);
    const [boardOrientation, setBoardOrientation] = useState('white');
    const [engineId, setEngineId]                 = useState("");
    const [username, setUsername]                 = useState("");
    const [gameEnd, setGameEnd]                   = useState(false);
    const [gameId, setGameId]                     = useState("");
    const [moveNum, setMoveNum]                   = useState(0);
    const [isLoading, setIsLoading]               = useState(false);
    const [isErr, setIsErr]                       = useState(true);
    const [ErrMessage, setErrMessage]             = useState("Please enter an Engine ID");

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
    
    const checkGame = (gameCheck) => {
        const possibleMoves = gameCheck.moves();
        console.log(possibleMoves);
        // exit if the game is over
        if (gameCheck.game_over() || gameCheck.in_draw() || possibleMoves.length === 0) {
            setGameEnd(true);
        }
    }

    function onDrop(sourceSquare, targetSquare) {

        const gameCopy = { ...game };
        const move = gameCopy.move({
            from: sourceSquare,
            to: targetSquare,
            promotion: 'q' // always promote to a queen for example simplicity
        });
        setGame(gameCopy);
        if (move === null) return false;

        //checkGame(gameCopy);
        const possibleMoves = gameCopy.moves();
        console.log(possibleMoves);
        // exit if the game is over
        if (gameCopy.game_over() || gameCopy.in_draw() || possibleMoves.length === 0) {
            setGameEnd(true);
        }

        setIsLoading(true);
        console.log(moveNum);
        makeMove(gameId, game.fen(), moveNum + 1)
        .then((resp) => {
            console.log(resp);
            try {
                console.log(game.moves());
                safeGameMutate((game) => {
                    game.load(resp.data.state);
                });
                const newPossibleMoves = game.moves();
                console.log(newPossibleMoves);
                // exit if the game is over
                if (game.game_over() || game.in_draw() || newPossibleMoves.length === 0) {
                    setGameEnd(true);
                }
                //checkGame(game);
                console.log(parseInt(resp.data.moveNum))
                setMoveNum(parseInt(resp.data.moveNum));
            } catch (err) {
                console.log("Calling the engine failed: %s\nPlaying random move", err);
                makeRandomMove();
                setMoveNum(moveNum + 2);
            }
            setIsLoading(false);
            return true;
        }).catch((err) => {
            console.log(err);
            setIsErr(true);
            setErrMessage("Failed to make engine move");

        });

        
    }

    const resetHandler = () => {
        setIsErr(false);
        safeGameMutate((game) => {
            game.reset();
            setMoveNum(0);
        });
        chessboardRef.current.clearPremoves();
    };

    const undoHandler = () => {
        setIsErr(false);
        safeGameMutate((game) => {
            game.undo();
        });
        chessboardRef.current.clearPremoves();
    };

    const newGameHandler = () => {
        setIsErr(false);
        if (engineId === '') {
            setIsErr(true);
            setErrMessage("Please enter an Engine ID");
        }
        // get new game ID
        setIsLoading(true);
        startGame(username, engineId)
        .then((newGameId) => {
            console.log(newGameId);
            setGameId(newGameId);
        })
        .catch((err) => {
            console.log(err);
            setIsErr(true);
            setErrMessage("Failed to create new game. Make sure that the engine ID is correct and try again");
        });

        safeGameMutate((game) => {
            game.reset();
        });
        setMoveNum(0);
        chessboardRef.current.clearPremoves();
        setGameEnd(false);
        setIsLoading(false);
    };

    return (
        <React.Fragment>
            <Stack sx={{alignItems: "center", marginTop: "40px"}} spacing={4}>
                <Stack direction="row" spacing={2}>
                    <TextField 
                        id="username" 
                        label="Guest Username" 
                        variant="standard"
                        value={username}
                        onChange={(event) => {
                            setUsername(event.target.value);
                        }} 
                    />
                    <TextField 
                        id="engineId" 
                        label="Engine ID" 
                        variant="standard"
                        value={engineId}
                        onChange={(event) => {
                            setEngineId(event.target.value);
                        }} 
                    />
                    <Button variant="contained" onClick={newGameHandler}>Start</Button>
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
                {isErr ? 
                (<Alert severity="error">{ErrMessage}</Alert>)
                :
                (<React.Fragment></React.Fragment>)
                }
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
            <Backdrop
                sx={{color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1}}
                open={gameEnd}
            >
                <Stack sx={{alignItems: 'center'}} spacing={4}>
                    <Typography>Game Over</Typography>
                    <Stack direction="row" >
                        <Button variant="contained" onClick={newGameHandler}>New Game</Button>
                        {/* Add button to display stats for game */}
                    </Stack>
                </Stack>
            </Backdrop>
            <Backdrop
                sx={{color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1, display: 'flex'}}
                open={isLoading}
            >
                <CircularProgress />
            </Backdrop>
        </React.Fragment>
    );
}