const { API_BASE_URL } = require('../constants');
// function to register server
fetch(API_BASE_URL + '/server')
    .then(response => {
        // indicates whether the response is successful (status code 200-299) or not
        if (!response.ok) {
            throw new Error(`Request failed with status ${response.status}`)
        }
        return response.json()
    })
    .then(data => {
        console.log(data.count)
        console.log(data.products)
    })
    .catch(error => console.log(error))