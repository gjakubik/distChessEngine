Parse = require('parse/node');
const constants = require('../constants');

// Initialize parse
Parse.initialize(constants.PARSE_APP_ID, constants.PARSE_JS_KEY);
Parse.serverURL = constants.PARSE_BASE_URL;

const create = async (gameId, state, moveNum) => {
    try {
        const myNewObject = new Parse.Object('Move');

        const Game = Parse.Object.extend('Game');
        const query = new Parse.Query(Game);
        const gameObj = await query.get(gameId);

        if (gameObj) {
            console.log("Found game");
            myNewObject.set('game', gameObj.toPointer());
            myNewObject.set('state', state);
            myNewObject.set('moveNum', moveNum);
        } else {
            console.log("Failed to find game");
            return "";
        }
        
        const result = await myNewObject.save();
        console.log(result);
        return result;
    } catch (error) {
        console.log(error);
        return "";
    }
};

try {
    const myNewObject = new Parse.Object('Game');
    myNewObject.set('username', username);
    console.log(username, engine1Id);
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
module.exports = { create }