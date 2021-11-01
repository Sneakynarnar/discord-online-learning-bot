const { createCanvas, loadImage} = require("canvas");
const width = 900;
const height = 200;
const canvas = createCanvas(width, height);
const ctx = canvas.getContext("2d");
const lvlThreshHold = 250
var username = "EliteNarNar#0001"
var position = 1
var totalXp = 100
var random = Math.floor(Math.random() * 101);
ctx.fillStyle = "#5b515c";
ctx.fillRect(0, 0, width, height)
ctx.fillStyle = "#00FF00"
ctx.font = "30px Impact";

ctx.fillText(username, 100, 100);
const buffer = canvas.toBuffer("image/png");
const fs = require("fs");
fs.writeFileSync("resources/temporaryfiles/rank.png", buffer);


