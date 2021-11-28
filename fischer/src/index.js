var net = require('net');

const handleConnection = (conn) => {    
    var remoteAddress = conn.remoteAddress + ':' + conn.remotePort;  
    console.log('new client connection from %s', remoteAddress);
    const onConnData = (d) => {
        const newData = d.toString('utf-8');
        console.log('connection data from %s: %j', remoteAddress, d);
        console.log('connection data from %s: %s', remoteAddress, newData);
        conn.write(d.length.toString());  
        conn.write(d);  
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

server.listen(5050, () => {    
    console.log('server listening to %j', server.address());  
});

