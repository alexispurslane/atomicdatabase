var wordwrap = require('wordwrap');
var linewrap = require('../');

var fs = require('fs');
var idleness = fs.readFileSync(__dirname + '/../test/idleness.txt', 'utf8');
var html = fs.readFileSync(__dirname + '/../test/html.txt', 'utf8');
var br = JSON.parse(fs.readFileSync(__dirname + '/../test/br.json', 'utf8')).text;


if (require.main === module) {
    var wrap, result;
    var time, diff, i, k, start, end;
    var mb, s;

    var tests = [linewrap(80), wordwrap(80), linewrap(10), wordwrap(10),
                 linewrap(20, 60), wordwrap(20, 60),
                 linewrap(30, {skipScheme: 'html'}),
                 linewrap(30, 60, {skipScheme: 'html'}),
                 linewrap(30, {lineBreakScheme: 'html'}),
                 linewrap(30, {skipScheme: 'html', lineBreakScheme: 'html'}),
                 linewrap(30, {lineBreakScheme: 'html', respectLineBreaks: 'none'})];

    var inputs = [idleness, idleness, idleness, idleness, idleness, idleness, html, html, br, br, br];
    var titles = ['linewrap(80), txt', 'wordwrap(80), txt', 'linewrap(10), txt',
                  'wordwrap(10), txt', 'linewrap(20, 60), txt', 'wordwrap(20, 60), txt',
                  'linewrap(30), html', 'linewrap(30, 60), html', 'linewrap(30), br',
                  'linewrap(30), br, skip', 'linewrap(30), br, no-respect'];
    var loops = [500, 500, 500, 500, 500, 500, 5000, 5000, 10000, 10000, 10000];

    start = parseInt(process.argv[2], 10) - 1;
    end = parseInt(process.argv[3], 10) - 1;
    if (start > end) {
        k = start;
        start = end;
        end = k;
    }
    if (!(start >= 0 && start < tests.length)) {
        start = 0;
    }
    if (!(end >= 0 && end < tests.length)) {
        end = tests.length - 1;
    }

    for (k = start; k <= end; k++) {
        console.log('Test %s: %s...', k+1, titles[k]);
        wrap = tests[k];
        time = process.hrtime();
        for (i = 0; i < loops[k]; i++) {
            result = wrap(inputs[k]);
        }
        diff = process.hrtime(time);
        mb = inputs[k].length * loops[k] / 1024 / 1024;
        s = diff[0] + diff[1]/1e9;
        console.log(mb/s + " MB/s: " + mb, " MB wrapped in " + s + " seconds.");
        console.log();
    }
}
