const express    = require('express');
const Parse      = require('parse/node');

const NAME_SERVER = 'catalog.cse.nd.edu'
const NS_PORT     = 9097

const app = express();

app.use(express.json());
app.set('view engine', 'pug');

// This renders the API homepage
app.get('/', (req, res) => {
    res.render('index');
});

app.post('/game', (req, res) => {
    // TODO: Find engine on nameserver

    // TODO: Send message to engine

    // TODO: Put game into Parse

    // TODO: Send back Game Id and 
});

// starting the server
app.listen(5050, () => {
    console.log('listening on port http://localhost:5050');
});
