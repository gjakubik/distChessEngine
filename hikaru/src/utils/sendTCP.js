const net = require('net');

const sendTCP = (host, port, message, timeout) => {
    return new Promise((resolve, reject) => {
        console.log(host, port, message, timeout);
        const socket = new net.Socket();

        const id = setTimeout(() => {
            clearTimeout(id);
            socket.destroy();
            reject("timed out");
            return;
        }, timeout);

        socket.connect({ host: host, port: port, family: 4 }, () => {
            console.log("connected to engine");
            socket.write(len(message));
            socket.write(message);
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