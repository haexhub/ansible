const express = require('express')
const app = express()
const port = 8765
const Gun = require('gun')

app.use(Gun.serve)
app.use(express.static(__dirname));

const server = app.listen(port, () => {
  console.log(`Gun server running on port ${port}🔥`)
})

Gun({ file:"./gunData", web: server })
