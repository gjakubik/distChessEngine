const { API_BASE_URL } = require('../constants');
import fetch from 'node-fetch';

const APIReq = async (endpoint, method, message) => {
    // function to register server
    const resp = fetch(API_BASE_URL + endpoint, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(message)
    });

    if (!resp.ok) {
        return {}
    }

    return resp.json()
};

module.exports = { APIReq }
