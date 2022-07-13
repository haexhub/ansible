'use strict';

const express = require('express');
const corsProxy = require('@isomorphic-git/cors-proxy/middleware.js')

// Constants
const PORT = 8080;
const HOST = '0.0.0.0';

// App
const app = express();
app.get('/', (req, res) => {
  res.send('Hello World');
});


const options = {
  port: PORT,
  insecure_origins: ["localhost:3000"]
}

app.use(corsProxy(options))