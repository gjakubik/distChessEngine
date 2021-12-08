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

After installing the dependencies for this project, you must find the location of the stockfish executable. Save this file's full path as it will need to be passed in as a command line argument in the next step.

Now, whenever you log on you will be able to activate this environment to run the project with `conda activate distChessEngine`.

#### *Spinning up a Master and Workers*
The backend of this chess engine is made up of a master node and several worker nodes, the runner files for which can be found in the `/harmon` directory. 
Before running the engine, you must allow the Stockfish distribution included in our repo to be executable. This can be done from the repository's root directory using the following command:
```bash
chmod +x /magnus/stockfish-10-linux/Linux/stockfish_10_x64
```

To run the engine you must run a master client and any number of worker clients. 
A master client can be started by navigating to the `/harmon` directory and running the `master_runner.py` file:
```bash
chmod +x master_runner.py
./master_runner.py OWNER PROJECT K ONLINE ELO
'''
The command-line arguments are defined as follows: 
* OWNER -- An ID for whoever is running the program. This will be saved on the Notre Dame catalog server.
* PROJECT -- A name for the cluster of clients you are deploying. This will be saved on the Notre Dame catalog server.
* K -- The number of workers you will deploy (or 0 if you want to run the engine as a single node)
* ONLINE -- 'True' if you want the engine to interface with our front-end React client, 'False' if you want to run the engine on its own in the command-line.
* ELO -- Argument to set the elo of the stockfish engine underneath our client. 

A worker client can be started by navigating to the `/harmon` directory and running the `worker_runner.py` file:
```bash
chmod +x worker_runner.py
./worker_runner.py OWNER PROJECT ID K ONLINE ELO ENGINE_ID
'''
The command-line arguments are defined as follows:
* OWNER -- An ID for whoever is running the engine cluster. Should be the same as what was used for the master client.
* PROJECT -- A name for the engine cluster being deployed. Should be the same as what was used for the master client.
* ID -- A numerical ID for this worker. Must be unique from the IDs of other workers in the cluster.
* K -- The number of workers being deployed in the cluster. Should be the same was what was used for the master client.
* ONLINE -- 'True' if you want the engine to interface with our front-end React client, 'False' otherwise. Should be the same as what was used for the master client
* ELO -- Argument to set the elo of the stockfish engine underneath the client.
* ENGINE_ID -- This field only needs to be set if the cluster is interfacing with the front-end. The master client will print out and engine_id it gets from our front-end server. That ID should be pasted into this field so the worker can properly communicate with the front-end.

### React Client

To start the react client, navigate to the `/


More specific instructions for each component of this project are found within the README of each of the folders linked above.

 
 ---
 <img src="https://www.chessprogramming.org/images/thumb/0/09/Stockfish-logo.png/300px-Stockfish-logo.png" width="25px" /> [Powered by Stockfish]

[Powered by Stockfish]: https://stockfishchess.org/
