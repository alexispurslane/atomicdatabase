var assert = require('assert');
var linewrap = require('../');

var fs = require('fs');
var content = fs.readFileSync(__dirname + '/br.json', 'utf8'),
    data = JSON.parse(content);
var brPat = /<\s*br(?:[\s/]*|\s[^>]*)>/i;

exports.stop30 = function () {
    var wrap = linewrap(30, {lineBreakScheme: 'html'}),
        wrapLF = linewrap(30, {lineBreakScheme: 'html', lineBreak: '\n'}),
        wrapNR = linewrap(30, {lineBreakScheme: 'html', respectLineBreaks: 'none'}),
        wrapS = linewrap(30, {skipScheme: 'html', lineBreakScheme: 'html'}),
        wrapSNR = linewrap(30, {skipScheme: 'html', lineBreakScheme: 'html', respectLineBreaks: 'none'});

    var text = data.text,
        res = wrap(text),
        resLF = wrapLF(text),
        resNR = wrapNR(text),
        resS = wrapS(text),
        resSNR = wrapSNR(text);

    assert.equal(res, data.res);
    assert.equal(resLF, data.resLF);
    assert.equal(resNR, data.resNR);
    assert.equal(resS, data.res);
    assert.equal(resSNR, data.resNR);

    assert.equal(/\n/.test(res), false);
    assert.equal(brPat.test(resLF), false);

    res.split(/<br>/).forEach(function (line) {
        assert.ok(line.length <= 30, 'line > 30 columns');
    });
    resLF.split(/\n/).forEach(function (line) {
        assert.ok(line.length <= 30, 'line > 30 columns');
    });
    resNR.split(/<br>/).forEach(function (line) {
        assert.ok(line.length <= 30, 'line > 30 columns');
    });
};
