var assert = require('assert');
var linewrap = require('../');

exports.wrapLineIndent = function() {
    var text = "  text sample with extraordinarily long word  ";
    var res = linewrap(10, {wrapLineIndent: 4})(text);
    assert.equal(res, "text\n    sample\n    with\n    extraordinarily\n    long\n    word");
};

exports.wrapLineIndentWithBase = function() {
    var text = "item1: this is a powerful item.\n second item: the second item.";
    var res = linewrap(2, 22, {wrapLineIndent: 2, wrapLineIndentBase: ':'})(text);
    assert.equal(res, "  item1: this is a\n         powerful\n         item.\n  second item: the\n               second\n               item.");
};

exports.preservedLineIndent = function() {
    var text = "  text sample with extraordinarily long word \n this is the second line. \n";
    var res = linewrap(10, {preservedLineIndent: 3, whitespace: 'all'})(text);
    assert.equal(res, "     text \nsample \nwith \nextraordinarily\n long word\n \n    this \nis the \nsecond \nline. \n   ");
};
