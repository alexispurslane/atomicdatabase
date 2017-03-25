var assert = require('assert');
var wordwrap = require('wordwrap');
var linewrap = require('../');

var fs = require('fs');
var idleness = fs.readFileSync(__dirname + '/idleness.txt', 'utf8');

exports.stop80 = function () {
    var res = wordwrap(80)(idleness),
        res2 = linewrap(80)(idleness);

//    assert.equal(res, res2);

    var lines2 = res2.split(/\n/);
    var words = idleness.split(/\s+/);
    lines2.forEach(function (line) {
        assert.ok(line.length <= 80, 'line > 80 columns');
        var chunks = line.match(/\S/) ? line.split(/\s+/) : [];
        assert.deepEqual(chunks, words.splice(0, chunks.length));
    });
};

exports.start20stop60 = function () {
    var res = wordwrap(20, 100)(idleness),
        res2 = linewrap(20, 100)(idleness);

//    assert.equal(res, res2);

    var lines2 = res2.split(/\n/);
    var words = idleness.split(/\s+/);
    lines2.forEach(function (line) {
        assert.ok(line.length <= 100, 'line > 100 columns');
        var chunks = line
            .split(/\s+/)
            .filter(function (x) { return x.match(/\S/); })
        ;
        assert.deepEqual(chunks, words.splice(0, chunks.length));
        assert.deepEqual(line.slice(0, 20), new Array(20 + 1).join(' '));
    });
};
