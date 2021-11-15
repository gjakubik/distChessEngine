# Chess API

## Game Server
This server is in the form of cloud code running on Parse servers. It handles communication between the GUI client and the engine clusters, which is what allows us to orchestrate a game across the system.

## Quickstart

To start the server, all that is needed is to run `npm start` while in the `/hikaru/` directory. If this is being run locally, it will be available at [`htpp://localhost:5050`](htpp://localhost:5050).

To deploy to production, make a pull request and contact [gjakubik](https://github.com/gjakubik)