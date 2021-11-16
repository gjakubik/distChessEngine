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

### Engine Client Setup

Note: This guide focuses on setup for the student machines at the Universtiy of Notre Dame. If you do not have an account, you will need to find a way to deploy to a cluster of machines. This can be achieved relatively easily(but probably not very cheaply) with virtual machines.

#### *Environment*
To run this project, it is be
First, log onto one of the student machines:
```bash
ssh <netID>@student00.cse.nd.edu
```

Now, install Miniconda if you haven't already:
```bash
curl https://repo.anaconda.com/miniconda/Miniconda3-py39_4.10.3-Linux-x86_64.sh > miniconda.sh
chmod 755 miniconda.sh
./miniconda.sh
```

Make sure to enter `yes` for the last step of installation to add `conda` to `PATH`.

You should now see `(base)` in front of your prompt, indicating that conda is working.

Now, create an environment called `distChessEngine` for the project:
```bash
conda create --name distChessEngine python=3.9
```

Once you have done this, navigate to the `/harmon/` directory. When you run an `ls`, you should see `requirements.txt`.

Download the dependencies by running:
```bash
pip install requirements.txt
```

This will install the necessary dependencies to run the engine.

Now, whenever you log on you will be able to activate this environment to run the project with `conda activate distChessEngine`.

#### *Spinning up a Master and Workers*

Todo for Michael

### React Client

To start the react client, navigate to the `/


More specific instructions for each component of this project are found within the README of each of the folders linked above.

 
 ---
 <img src="https://www.chessprogramming.org/images/thumb/0/09/Stockfish-logo.png/300px-Stockfish-logo.png" width="25px" /> [Powered by Stockfish]

[Powered by Stockfish]: https://stockfishchess.org/
