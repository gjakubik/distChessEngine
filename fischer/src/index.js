const net = require('net');
const { APIReq } = require('./utils/APIReq');

var conns = {};

const sendMessage = (conn, message) => {
    conn.write(message.length.toString().padEnd(64 - message.length.toString().length, " "));  
    conn.write(message);
}

const handleConnection = (conn) => {    
    var remoteAddress = conn.remoteAddress + ':' + conn.remotePort;  
    console.log('new client connection from %s', remoteAddress);
    conn.setEncoding('utf8');
    conns[remoteAddress] = conn;
    // New connection, register new enginge
    const onConnData = (d) => {
        const newData = JSON.parse(d);
        console.log('data length from %s: %d', remoteAddress, d.length);
        console.log('data data from %s: ', remoteAddress, newData);
        console.log('data sending length to %s: %s', remoteAddress, d.length.toString().padEnd((64 - d.length.toString().length), "*"));
        // If endpoint is empty then this is a new move from the user
        try {
            if (newData.endpoint === "" ) {
                console.log('::ffff:'+newData.host + ':' + newData.port);
                console.log(Object.keys(conns));
                const engineConn = conns['::ffff:'+newData.host + ':' + newData.port];
                sendMessage(engineConn, JSON.stringify(newData))
            } else {
                if (newData.endpoint === "/move") {
                    // if the endpoint is move it is move response from engine, update API
                    console.log(conns);
                    const APIConn = conns['::ffff:127.0.0.1:'+newData.apiPort]
                    APIConn.write(JSON.stringify(newData));
                    conn.sendMessage("OK"); 
                } else {
                    // If the endpoint is otherwise, it is master or worker registering
                    APIReq(newData['endpoint'], newData['method'], newData)
                    .then((resp) => {
                        console.log(resp);
                        sendMessage(conn, JSON.stringify(resp));
                    })
                    .catch((err) => console.log(err));
                }
            }
        } catch (err) {
            console.log(err);
        }
    }

    const onConnClose = () => {  
        console.log('connection from %s closed', remoteAddress);  
    }

    const onConnError = (err) => {  
        console.log('Connection %s error: %s', remoteAddress, err.message);  
    }  
    conn.on('data', onConnData);  
    conn.once('close', onConnClose);  
    conn.on('error', onConnError);
    
}

var server = net.createServer();    
server.on('connection', handleConnection);

server.listen(5051, () => {    
    console.log('server listening to %j', server.address());  
});

