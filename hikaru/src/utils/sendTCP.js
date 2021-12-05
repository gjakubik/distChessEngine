const net       = require('net');
const constants = require('../constants');

const sendTCP =  (message, timeout) => {
    return new Promise((resolve, reject) => {
        
        const socket = new net.Socket();
        console.log(socket);
        const id = setTimeout(() => {
            clearTimeout(id);
            socket.destroy();
            reject("timed out");
            return;
        }, timeout);

        console.log("Attempting to connect");
        socket.connect(constants.TCP_GATE_PORT , constants.TCP_GATE_HOST, () => {
            console.log("connected to engine");
            socket.write(JSON.stringify(message));
        });

        socket.on("data", data => {
            console.log("Recieved data: ", data.toString('utf-8'));
            resolve(data.toString('utf-8'));
            clearTimeout(id);
            socket.destroy();
            return;
        });

        socket.on("error", err => {
            reject(err);
            return;
        });

        
    })
};

module.exports = { sendTCP }