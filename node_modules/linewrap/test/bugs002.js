var assert = require('assert');
var linewrap = require('../');

// Exposes bugs in linewrap 0.0.2
exports.bug1 = function() {
    var text = "I love u\n\n\n";
    var res = linewrap(10)(text);
    assert.equal(res, "I love u\n\n\n");
};

exports.bug2 = function() {
    var text = "I hug you, my friend";
    var res = linewrap(10)(text);
    assert.equal(res, "I hug you,\nmy friend");
};

exports.bug3 = function() {
    var text = "I love u\n\n\n";
    var res = linewrap.hard(10)(text);
    assert.equal(res, "I love u\n\n\n");
};

exports.bug4 = function() {
    var text = "I hug you, my friend";
    var res = linewrap.hard(10)(text);
    assert.equal(res, "I hug you,\nmy friend");
};

exports.bug5 = function() {
    var text = "12345678910";
    var res = linewrap(10)(text);
    assert.equal(res, "12345678910");
};

exports.bug6 = function() {
    var text = "\n12345678910\n";
    var res = linewrap(1, 11)(text);
    assert.equal(res, " \n 12345678910\n ");
};
