const net       = require('net');

const sendTCP = (host, port, conns, message) => {
    return new Promise((resolve, reject) => {
        
        const socket = conns[host + ':' + port]

        socket.write(message.length.toString().padEnd(64 - strResp.length.toString().length, " "));  
        socket.write(message);

        
    })
};

module.exports = { sendTCP }