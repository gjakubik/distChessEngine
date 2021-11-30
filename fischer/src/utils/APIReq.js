const { API_BASE_URL } = require('../constants');
const fetch = require('cross-fetch');

const APIReq = async (endpoint, method, message) => {
    // function to register server
    const resp = fetch(API_BASE_URL + endpoint, {
        method: method,
        mode: 'same-origin',
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
