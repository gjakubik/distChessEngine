# Distributed Chess Engine
#### _Distributed Systems Fall 2021_

![GitHub last commit](https://img.shields.io/github/last-commit/gjakubik/distChessEngine?style=for-the-badge) ![GitHub commit activity](https://img.shields.io/github/commit-activity/w/gjakubik/distChessEngine?style=for-the-badge)

This project allows you to play against our custom distributed chess engine and see if you can beat it! If you aren't up to the test you can always simulate it against itself and see if you can find a winning configuration!

## Features
- Distributed chess engine server
- GUI client
    - Play the engine yourself
    - Watch it play itself
    - Game metrics for different configurations
- Custom API to communicate between engine and GUI
    - Parse backend to handle game states 

## Structure
|                       | Codebase              |      Description          |
| :-------------------- |:--------------------  | :-----------------------: |
| <img src="https://i.pinimg.com/originals/2c/95/04/2c950491f152f19fd03ee608cf08bbe1.jpg" width="50px" /> | [harmon](harmon)  |      Chess Engine     |
| <img src="https://players.chessbase.com/picture/hes24061" width="50px" />                               | [hess](hess)      |     React Frontend    |
| <img src="https://www.tatasteelchess.in/sites/default/files/2018-09/nakamura.jpg" width="50px" />       | [hikaru](hikaru)  |   Game Management API | 
 
 ## Getting Started

The specific instructions for each component of this project are found within the README of each of the folders linked above.

 
 ---
 <img src="https://www.chessprogramming.org/images/thumb/0/09/Stockfish-logo.png/300px-Stockfish-logo.png" width="25px" /> [Powered by Stockfish]

[Powered by Stockfish]: https://stockfishchess.org/
