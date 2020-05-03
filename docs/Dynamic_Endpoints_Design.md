# Dynamic Endpoints Interface (WIP)
Originally AVS SDK comes with the Sample Application that supports 1 endpoint. The purpose of this interface is to enable multiple endpoints per application.

# Components
1. AVS application
2. JSON file containg a list of all devices and their GPIO connections. Each key is the `endpointId` used to create each endpoint in the application.
    - An example of a JSON file:
        `{
            "desk_00": {
                "friendlyName": "Stand up desk"
                "isConnected": true,    // status of the endpoint
                "pins": [00, 01, 02, 03]  // this endpoint uses 4 pins
            },
            "toy_00": {
                "friendlyName": "Musical toy"
                "isConnected": true,  
                "pins": [04, 05]  
            },
            .
            .
            .
            "endpoint_N": {
                "isConnected": false,    // status of the endpoint
                "pins": [] 
            },
        }`
3. A module to read the JSON file (2)

# Implementation
The JSON Reader Module (3) utilizes a common library to read the file (2) and iterates over all of the endpoint key and return a structure containing the necessary information for the AVS' `Endpoint Builder` module to create the endpoints.