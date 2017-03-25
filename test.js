const nlp = require("compromise");
const process = require("process");

const stdin = process.openStdin();

stdin.addListener("data", function(d) {
    let data = nlp(d.toString().trim()).terms().data();
    data.forEach((d) => {
        console.log(d.bestTag+": "+d.normal+" ("+d.tags.join(", ")+")");
    });
});

/*
  (father Person Parent)
  (father Parent Grandparent)
  (grandfather Person Grandparent)
*/

/*
  the father of Person is Parent,
  the father of Parent is Grandparent,
  the grandfather of Person was Grandparent
*/
