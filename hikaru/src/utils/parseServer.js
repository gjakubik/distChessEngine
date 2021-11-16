const Parse   = require('parse/node');

// Initialize parse
Parse.initialize('gUpraAvGUv44Gl88sFR7DiDpuWGCl4z59xeP8PgW', 'b1rryIdHNtOJh2b5OlOx6uxpbRRRVQN5NVCt0mYk');
Parse.serverURL = 'https://parseapi.back4app.com/';

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
        return ""
    }
};

// Return server response object on success, null on failure
const get = async (serverId) => {
    const Server = Parse.Object.extend('Server');
    const query = new Parse.Query(Server);
    try {
        const result = query.equalTo("objectId", serverId);
        const serverObj = {
            "id":            result.id,
            "host":          result.get('host'),
            "port":          result.get('port'),
            "numWorkers":    result.get('numWorkers'),
            "droppedWorker": result.get('droppedWorker')
        };

        return serverObj;
    } catch (error) {
        return null
    }
};

module.exports = { create, get }