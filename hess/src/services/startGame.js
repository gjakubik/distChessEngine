import https from 'https';
import axios from 'axios';
import { resolve } from 'path';

const API_BASE_URL = 'https://gavinjakubik.me:5050/'
const endpoint = 'game/'
// This function will send the users move to the API and return the response move
export default function startGame(username, engineId) {
    return new Promise((resolve, reject) => {
        try {
            const message = {
                "username": username,
                "engine1Id": engineId,
                "engine2Id": "",
                "endpoint": ""
            };
            console.log(message);
            const headers = {
                'Content-Type': 'text/plain',
                'Access-Control-Allow-Origin': "*",
            }
    
            axios.post(API_BASE_URL + endpoint, JSON.stringify(message), { headers: headers})
                .then((resp) => {
                    console.log(resp);
                    console.log(resp.data);
                    console.log(resp.data.gameId);
                    resolve(resp.data.gameId);
                })
                .catch((err) => {
                    console.log(err);
                    reject("");
                });
            /*
            // function to register server
           fetch(API_BASE_URL + endpoint, {
                method: 'POST',
                mode: 'no-cors',
                headers: {
                    'Content-Type': 'text/plain'
                },
                body: JSON.stringify(message),
                httpsAgent: httpsAgent
            })
                .then((resp) => {
                    console.log(resp);
                    return resp.json().gameId;
                })
                .catch((err) => {
                    console.log(err);
                    return "";
                });
            */
        } catch (err) {
            console.log(err);
            resolve("");
        }
    })
    
}