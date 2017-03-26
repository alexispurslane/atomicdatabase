const nlp = require("compromise");
const process = require("process");

console.log(nlp(process.argv[2]).terms().data().map((d) => d.tags));
console.log(nlp(process.argv[2]).match(process.argv[3]).found);
