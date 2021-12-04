import https from 'https';

const API_BASE_URL = 'https://gavinjakubik.me:5050/'
const endpoint = 'move/'
// This function will send the users move to the API and return the response move
export default async function makeMove(gameId, state, moveNum) {
    try {
        const httpsAgent = new https.Agent({
            rejectUnauthorized: false,
        });
        const message = {
            "gameId": gameId,
            "state": state,
            "moveNum": moveNum,
            "endpoint": "",
            "color": "black"
        };
        // function to register server
        console.log(message);

        const headers = {
            'Content-Type': 'text/plain',
            'Access-Control-Allow-Origin': "*",
        }

        axios.post(API_BASE_URL + endpoint, JSON.stringify(message), { headers: headers})
            .then((resp) => {
                console.log(resp);
                return resp.json();
            })
            .catch((err) => {
                console.log(err);
                return "";
            });
        /*
        const resp = await fetch(API_BASE_URL + endpoint, {
            method: 'POST',
            mode: 'no-cors',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(message),
            agent: httpsAgent
        });
    
        if (!resp.ok) {
            console.log()
            return {}
        }
        console.log(resp.json());
        return resp.json()
        */
    } catch (err) {
        console.log(err);
        return {}
    }
}