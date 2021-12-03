const { API_BASE_URL } = require('../constants');
const https = require('https');
const fetch = require('cross-fetch');

const APIReq = async (endpoint, method, message) => {

    const httpsAgent = new https.Agent({
        rejectUnauthorized: false,
    });
    // function to register server
    var opts = {
        method: method,
        mode: 'no-cors',
        headers: {
            'Content-Type': 'text/plain'
        },
        agent: httpsAgent
    };
    console.log(opts);
    if ( method != 'GET' ) {
        console.log('not a get req');
        opts = {...opts, body: JSON.stringify(message)}
    }

    const resp = await fetch(API_BASE_URL + endpoint, opts);

    if (!resp.ok) {
        console.log()
        return {}
    }

    return resp.json()
};

module.exports = { APIReq }
