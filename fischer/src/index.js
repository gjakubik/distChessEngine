const net = require('net');
const APIReq = require('./utils/APIReq');

const handleConnection = (conn) => {    
    var remoteAddress = conn.remoteAddress + ':' + conn.remotePort;  
    console.log('new client connection from %s', remoteAddress);
    conn.setEncoding('utf8');
    // New connection, register new enginge
    const onConnData = (d) => {
        const newData = JSON.parse(d);
        console.log('connection length from %s: %d', remoteAddress, d.length);
        console.log('connection data from %s: ', remoteAddress, newData);
        console.log('connection sending length to %s: %s', remoteAddress, d.length.toString().padEnd((64 - d.length.toString().length), "*"));

        // Send the request to the API
        APIReq(newData['endpoint'], newData['method'], newData)
            .then((resp) => {
                const strResp = JSON.stringify(resp);
                conn.write(strResp.length.toString().padEnd(64 - strResp.length.toString().length, " "));  
                conn.write(JSON.stringify(resp));
            })
            .catch((err) => console.log(err));
          
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

