const Parse     = require('parse/node');
const constants = require('../constants');

// Initialize parse
Parse.initialize(constants.PARSE_APP_ID, constants.PARSE_JS_KEY);
Parse.serverURL = constants.PARSE_BASE_URL;

// TODO: Add support for 2 engines
// Return id string on success and empty on fail
const create = async (username, engine1Id, engine2Id) => {
    try {
        const myNewObject = new Parse.Object('Game');
        myNewObject.set('username', username);

        const Server = Parse.Object.extend('Server');
        console.log(engine1Id)
        const query = new Parse.Query(Server);
        const engine1Obj = await query.get(engine1Id);

        console.log(engine1Obj);
        if (engine1Obj) {
            console.log("Found server");
            myNewObject.set('engine1', engine1Obj.toPointer());
        } else {
            console.log("Failed to find server");
            return "";
        }
        
        const result = await myNewObject.save();
        console.log(result);
        return result.id;
    } catch (error) {
        console.log(error);
        return "";
    }
};

// Return game object on success
const get = async (gameId) => {
    const Game = Parse.Object.extend('Game');
    const query = new Parse.Query(Game);
    
    try {
        const results = await query.equalTo("objectId", gameId);
        
        const gameObj = {
            "username": object.get('username'),
            "winner": object.get('winner'),
            "engine1": object.get('engine1').id,
            "engine2": object.get('engine2').id
        }

        return gameObj;
        
    } catch (error) {
        console.error('Error while fetching Game', error);
        return null;
    }
};

module.exports = { create, get }