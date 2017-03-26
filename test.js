const nlp = require("compromise");
const process = require("process");

console.log(nlp("What is the age of Wrex?").match("#Noun #Preposition #Noun").found);
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
