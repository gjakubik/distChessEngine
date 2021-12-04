const { assert } = require('console');
const express = require('express');
const fs      = require('fs');
const https   = require('https');
const net     = require('net');
const cors    = require('cors');
const server  = require('./utils/parseServer');
const game    = require('./utils/parseGame');
const move    = require('./utils/parseMove');
const tcp     = require('./utils/sendTCP');

// Initialize express app
const app = express();
app.use(express.json({
    type: ['application/json', 'text/plain']
  }));
app.use(cors())

// Set view engine for home route html rendering
app.set('view engine', 'pug');

// This renders the API homepage
app.get('/', (req, res) => {
    res.render('index');
});

app.post('/game', async (req, res) => {
    // Make sure request is valid
    console.log(req.body);
    try {
        assert(true, req.body.username);
        assert(true, req.body.engine1Id);
    } catch (e) {
        console.log(e);
        res.status(400).send("Bad request data");
        return;
    }
    // Find engine in server list
    console.log("Finding Engine")
    const servObj = await server.get(req.body.engine1Id);

    if (servObj == null) {
        res.status(401).send("Engine Id not found");
        return;
    }

    console.log("Creating parse game")
    // Put game into Parse
    var err = "";
    const gameId = await game.create(req.body.username, req.body.engine1Id, req.body.engine2Id)
        .catch((error) => {
            err = error;
        });
    
    if (err !== "") {
        res.status(400).send(err);
        return;
    };

    if (gameId === "") {
        res.status(402).send("Creation of game failed");
        return;
    };
    console.log(JSON.stringify({"gameId": gameId}));
    res.status(200).send(JSON.stringify({"gameId": gameId}));

    /*
    console.log("sending message to engine");
    const serverObj = await server.get(req.body.engine1Id);
    // Send gameId to engine
    const message = {
        "owner": req.body.username,
        "type": "game_id",
        "gameId": gameId,
        "endpoint": "",
        "host": serverObj.host,
        "port": serverObj.port
    }
    
    if (err !== "") {
        res.status(400).send(err);
        return;
    }

    // Send back gameId
    if (resp === 'OK') {
        res.status(200).send({"gameId": gameId});
        return;
    } else {
        res.send("Engine declined game");
    }
    */
});

app.post('/move', async (req, res) => {
    try {
        console.log("moving");
        // TODO: Put user move in parse
        const playerMove = await move.create(req.body.gameId, req.body.state, req.body.moveNum);
        const gameObj = await game.get(req.body.gameId);
        const serverObj = await server.get(gameObj.engine1);
        const message = {
            ...req.body,
            "host": serverObj.host,
            "port": serverObj.port
        }
        // TODO: Send move to engine
        const engineResp = await tcp.sendTCP(message);

        // TODO: Put engine move in parse
        const engineMove = await move.create(req.body.gameId, engineResp.state, engineResp.moveNum);
        // TODO: Send engine move as response to user
        res.status(200).send(engineResp);
    } catch (err) {
        res.status(400).send("Error sending move to server: ", err);
    }
    

});

app.post('/server', async (req, res) => {
    // Make sure request is valid
    try {
        assert(true, req.body.host);
        assert(true, req.body.port);
        assert(true, req.body.numWorkers);
    } catch (e) {
        console.log(e);
        res.status(400).send("Bad request data");
        return;
    }
    // Put server into parse
    const engineId = await server.create(req.body.host, req.body.port, req.body.numWorkers);
    // Respond with engineId
    res.status(200).send({"engineId": engineId});
})

app.get('/server/:engineId', async (req, res) => {
    const resp = await server.get(req.params.engineId);

    if (!resp) {
        res.status(400).send("Could not find info for engineId: ", req.params.engineId);
        return;
    }

    res.status(200).send(resp);
})

// starting the server
https.createServer({
    key: fs.readFileSync('/etc/letsencrypt/live/gavinjakubik.me/privkey.pem'),
    cert: fs.readFileSync('/etc/letsencrypt/live/gavinjakubik.me/cert.pem')
}, app).listen(5050, () => {
    console.log('listening on port https://gavinjakubik.me:5050');
})
