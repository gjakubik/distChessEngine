const { assert } = require('console');
const express = require('express');
const fs      = require('fs');
const https   = require('https');
const net     = require('net');
const server  = require('./utils/parseServer');
const game    = require('./utils/parseGame');

// Initialize express app
const app = express();
app.use(express.json());

// Set view engine for home route html rendering
app.set('view engine', 'pug');

// This renders the API homepage
app.get('/', (req, res) => {
    res.render('index');
});

app.post('/game', async (req, res) => {
    // Make sure request is valid
    try {
        assert(true, req.body.username);
        assert(true, req.body.engine1Id);
        assert(true, req.body.engine2Id);
    } catch {
        res.status(400).send("Bad request data");
        return;
    }
    // Find engine in server list - Unnecessary?
    const servObj = await server.get(req.body.engine1Id);

    if (servObj == null) {
        res.status(401).send("Engine Id not found")
    }

    // TODO: Put game into Parse
    const gameId = await game.create(username, engine1Id, engine2Id);

    if (gameId === "") {
        res.status(402).send("Creation of game failed");
        return;
    }

    // Send gameId to engine
    const client = new net.Socket();
    client.connect({ host: servObj.host, port: servObj.port }, () => {
        client.write(gameId);
    });

    var resp = '';
    // Catch response from engine and check
    client.on('data', (data) => {
        resp = data.toString('utf-8');
        console.log(resp);
        client.destroy();
    })

    // Send back gameId
    if (resp === 'OK') {
        res.status(200).send({"gameId": gameId});
    } else {
        res.status(403).send("Engine declined game");
    }
});

app.post('/move', (req, res) => {
    // TODO: Put user move in parse

    // TODO: Send move to engine

    // TODO: Get response from engine

    // TODO: Put engine move in parse

    // TODO: Send engine move as response to user

});

app.post('/server', async (req, res) => {
    // Make sure request is valid
    try {
        assert(true, req.body.host);
        assert(true, req.body.port);
        assert(true, req.body.numWorkers);
    } catch {
        res.status(400).send("Bad request data");
        return;
    }
    // Put server into parse
    const engineId = await server.create(req.body.host, req.body.port, req.body.numWorkers);
    // Respond with engineId
    res.status(200).send({"engineId": engineId});
})

// starting the server
https.createServer({
    key: fs.readFileSync('server.key'),
    cert: fs.readFileSync('server.cert')
}, app).listen(5050, () => {
    console.log('listening on port https://gavinjakubik.me:5050');
})
