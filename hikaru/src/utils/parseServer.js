const Parse   = require('parse/node');
const constants = require('../constants');

// Initialize parse
Parse.initialize(constants.PARSE_APP_ID, constants.PARSE_JS_KEY);
Parse.serverURL = constants.PARSE_BASE_URL;

// Return id string on success and empty on fail
const create = async (host, port, numWorkers) => {
    const myNewObject = new Parse.Object('Server');
    myNewObject.set('host', host);
    myNewObject.set('port', port);
    myNewObject.set('numWorkers', numWorkers);
    try {
        const result = await myNewObject.save();
        return result.id
    } catch (error) {
        console.log(error);
        return ""
    }
};

const update = async (engineId, host, port, numWorkers) => {
    const Server = Parse.Object.extend('Server');
    const query = new Parse.Query(Server);

    try {
        const res = await query.get(engineId);

        res.set('host', host);
        res.set('port', port);
        res.set('numWorkers', numWorkers);
        console.log("updating server info...");
        const newServer = await res.save();
        console.log("Info updated");
    } catch (err) {
        console.log(err);
    }
}

// Return server response object on success, null on failure
const get = async (serverId) => {
    const Server = Parse.Object.extend('Server');
    const query = new Parse.Query(Server);
    console.log(serverId);
    try {
        const result = await query.get(serverId);
        const serverObj = {
            "id":            result.id,
            "host":          result.get('host'),
            "port":          result.get('port'),
            "numWorkers":    result.get('numWorkers'),
            "droppedWorker": result.get('droppedWorker')
        };

        return serverObj;
    } catch (error) {
        console.log(error);
        return null
    }
};

module.exports = { create, get, update }