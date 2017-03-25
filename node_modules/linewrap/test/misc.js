var assert = require('assert');
var linewrap = require('../');

exports.bulge = function() {
    var text = "  text sample with extraordinarily long word  ";
    var res = linewrap(10, {whitespace: 'all'})(text);
    assert.equal(res, "  text \nsample \nwith \nextraordinarily\n long word\n  ");
};

exports.blankline = function() {
    var text = "    \n  text sample";
    var res = linewrap(2, 12, {whitespace: 'line'})(text);
    assert.equal(res, "  \n    text\n  sample");
};

exports.hardblank = function() {
    var text = "              text sample";
    var res = linewrap.hard(2, 12, {whitespace: 'line'})(text);
    assert.equal(res, "  \n      text\n  sample");
};

exports.multiline = function() {
    var text = "   text   \n            \n   text   \n";
    var res = linewrap.hard(10, {whitespace: 'line'})(text);
    assert.equal(res, "   text\n\n\n   text\n");
};

exports.colorall = function() {
    var text = "text text\x1B[1;2;3m      ";
    var res = linewrap(10, {skipScheme: 'ansi-color', whitespace: 'all'})(text);
    assert.equal(res, "text text\x1B[1;2;3m \n     ");
};

exports.colorall2 = function() {
    var text = "the \x1B[1;2;3mextraordinarily\x1B[0m long word";
    var res = linewrap(10, {skipScheme: 'ansi-color', whitespace: 'all'})(text);
    assert.equal(res, "the \x1B[1;2;3m\nextraordinarily\n\x1B[0m long word");
};

exports.cleanvsnew = function() {
    var text = " text text  <tag>  text";
    var res = linewrap.hard(10, {skipScheme: 'html', whitespace: 'line'})(text);
    assert.equal(res, " text text\n<tag>text");
};

exports.collapse = function() {
    var text = "  text  text  \n  \n text  ";
    var res = linewrap(10, {whitespace: 'collapse', respectLineBreaks:'s2'})(text);
    assert.equal(res, "text text\ntext");
};

exports.wrapall = function() {
    var text = "  text                                      text    ";
    var res = linewrap(10, {whitespace: 'all'})(text);
    assert.equal(res, "  text    \n          \n          \n          \n    text  \n  ");
};

exports.wrapline = function() {
    var text = "  text          \n                         text    ";
    var res = linewrap(10, {whitespace: 'line'})(text);
    assert.equal(res, "  text\n\n\n     text");
};
