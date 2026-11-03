// Régénère roblox/ElastiqueAnimations.lua depuis elastique.js (équivalent de ELASTIC.toLuau() dans le visualiseur).
// Usage : node regenerer_luau.js   puis   python -I adapter_sequences.py
const fs = require("fs");
const path = require("path");
global.window = {};
eval(fs.readFileSync(path.join(__dirname, "elastique.js"), "utf8"));
fs.writeFileSync(path.join(__dirname, "roblox", "ElastiqueAnimations.lua"), window.ELASTIC.toLuau());
console.log("roblox/ElastiqueAnimations.lua régénéré");
