var assert = require('assert');
var linewrap = require('../');

var fs = require('fs');
var textBL = fs.readFileSync(__dirname + '/paragraph.txt', 'utf8'),
    resultBL = fs.readFileSync(__dirname + '/paragraph-res.txt', 'utf8'),
    textID = fs.readFileSync(__dirname + '/paragraph2.txt', 'utf8'),
    resultID = fs.readFileSync(__dirname + '/paragraph2-res.txt', 'utf8');

exports.blankline = function () {
    var wrap = linewrap(80, {respectLineBreaks:'multi', whitespace:'line'}),
        res = wrap(textBL);

    assert.equal(res, resultBL);

    res.split(/\n/).forEach(function (line) {
        assert.ok(line.length <= 80, 'line > 80 columns');
        if (line.length > 0) {
            assert.ok(line[line.length - 1] !== ' ', 'trailing space not stripped');
        }
    });
};

exports.identation = function () {
    var wrap = linewrap(80, {respectLineBreaks:'s4', whitespace:'line'}),
        res = wrap(textID);

    assert.equal(res, resultID);

    res.split(/\n/).forEach(function (line) {
        assert.ok(line.length <= 80, 'line > 80 columns');
        if (line.length > 0) {
            assert.ok(line[line.length - 1] !== ' ', 'trailing space not stripped');
        }
    });
};
