var assert = require('assert');
var linewrap = require('../');

var fs = require('fs');
var text = fs.readFileSync(__dirname + '/html.txt', 'utf8'),
    result = fs.readFileSync(__dirname + '/html-res.txt', 'utf8');

exports.html_skip = function () {
    var wrap = linewrap(30, {skipScheme: 'html'}),
        res = wrap(text);

    assert.equal(res, result);

    res.split(/\n/).forEach(function (line) {
        line = line.replace(/<[^>]*>/g, '');
        assert.ok(line.length <= 30, 'line > 30 columns');
    });
};
