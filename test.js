const nlp = require("compromise");
const process = require("process");

console.log(nlp(process.argv[2]).match(process.argv[3]).found);
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
