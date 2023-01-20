const path = require('path');
module.exports = {
  mode: "production",
  entry: "./puppeteer.js",
  target: "node",
  output: {
    path: path.resolve(__dirname),
    filename: "puppeteer.production.min.js"
  }
};
