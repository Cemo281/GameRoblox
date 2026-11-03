// Régénère roblox/SabreurAnimations.lua depuis anims.js (équivalent de SABRE.toLuau() dans le visualiseur).
// Usage : node regenerer_luau.js   puis   python -I adapter_sequences.py
const fs = require("fs");
const path = require("path");
global.window = {};
eval(fs.readFileSync(path.join(__dirname, "anims.js"), "utf8"));
fs.writeFileSync(path.join(__dirname, "roblox", "SabreurAnimations.lua"), window.SABRE.toLuau());
console.log("roblox/SabreurAnimations.lua régénéré");
