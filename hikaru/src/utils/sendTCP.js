const net = require('net');

const sendTCP = (host, port, message, timeout) => {
    return new Promise((resolve, reject) => {
        
        const socket = new net.Socket();

        const id = setTimeout(() => {
            clearTimeout(id);
            socket.destroy();
            reject("timed out");
            return;
        }, timeout);

        socket.connect({ port: port }, host, () => {
            console.log("connected to engine");
            socket.write(len(message));
            socket.write(message);
        });

        console.log("data handler");
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