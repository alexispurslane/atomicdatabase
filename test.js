const nlp = require("compromise");
const process = require("process");

const stdin = process.openStdin();

stdin.addListener("data", function(d) {
    let data = nlp(d.toString().trim()).terms().data();
    data.forEach((d) => {
        console.log(d.bestTag+": "+d.normal+" ("+d.tags.join(", ")+")");
    });
});
