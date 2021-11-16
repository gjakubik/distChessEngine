const Parse  = require('parse/node');

// Initialize parse
Parse.initialize('gUpraAvGUv44Gl88sFR7DiDpuWGCl4z59xeP8PgW', 'b1rryIdHNtOJh2b5OlOx6uxpbRRRVQN5NVCt0mYk');
Parse.serverURL = 'https://parseapi.back4app.com/';

// TODO: Add support for 2 engines
// Return id string on success and empty on fail
const create = async (username, engine1Id, engine2Id) => {
    const myNewObject = new Parse.Object('Game');
    myNewObject.set('username', username);

    const Server = Parse.Object.extend('Server');
    const query = new Parse.Query(Server);

    const engine1 = query.equalTo("objectId", engine1Id);

    myNewObject.set('engine1', engine1);
    try {
        const result = await myNewObject.save();
        return result.id;
    } catch (error) {
        return "";
    }
};

// Return server response object on success, null on failure
const get = async (serverId) => {
    const Server = Parse.Object.extend('Server');
    const query = new Parse.Query(Server);
    try {
        const result = query.equalTo("objectId", serverId);
        const serverObj = {
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