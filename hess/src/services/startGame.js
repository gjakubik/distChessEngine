import https from 'https';
import axios from 'axios';

const API_BASE_URL = 'https://gavinjakubik.me:5050'
const endpoint = '/game'
// This function will send the users move to the API and return the response move
export default async function startGame(username, engineId) {
    try {
        const httpsAgent = new https.Agent({
            rejectUnauthorized: false,
        });
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
                return resp.json().gameId;
            })
            .catch((err) => {
                console.log(err);
                return "";
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
        return "";
    }
}