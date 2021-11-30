import https from 'https';

const API_BASE_URL = 'https://gavinjakubik.me:5050/'
const endpoint = 'game/'
// This function will send the users move to the API and return the response move
export default async function startGame(username, engineId) {
    try {
        const httpsAgent = new https.Agent({
            rejectUnauthorized: false,
        });
        const message = {
            "username": username,
            "engine1Id": engineId,
            "engine2Id": ""
        };
        console.log(message);
        // function to register server
        const resp = await fetch(API_BASE_URL + endpoint, {
            method: 'POST',
            mode: 'no-cors',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(message),
            httpsAgent: httpsAgent
        });
    
        if (!resp.ok) {
            console.log()
            return {}
        }
    
        return resp.json().gameId
    } catch (err) {
        console.log(err);
        return {}
    }
}