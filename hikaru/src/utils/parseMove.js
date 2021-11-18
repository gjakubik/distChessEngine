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
        const gameObj = await query.get(gameId).catch((error) => {
            console.log(error);
        });

        if (gameObj) {
            console.log("Found game");
            myNewObject.set('game', gameObj.toPointer());
            myNewObject.set('state', state);
            myNewObject.set('moveNum', moveNum);
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