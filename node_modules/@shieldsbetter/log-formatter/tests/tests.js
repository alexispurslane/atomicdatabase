var assert = require('chai').assert;
var colors = require('colors');
var fs = require('fs');
var differ = require('diff');
var relFile = require('read-file-relative').readSync;

var lf;

var prefix = 'prefix: ';
var loremIpsum = relFile('loremIpsum.txt').trim();
var singleLine = 'A single line.';
var brokenLine = 'Broken\n' + loremIpsum + '\nLine';

var golden4Indent = relFile('golden4indent.txt').trim() + '\n';
var golden3Indent70wrap = relFile('golden3indent70wrap.txt').trim() + '\n';

var output = '';

function log(line) {
	output += line + '\n';
}

function resetLog() {
	output = '';
}

function doStandardSequence(t) {
	t.log(prefix, loremIpsum);
	t.log(loremIpsum);
	t.log(prefix, loremIpsum);

	t.begin();
	t.log(prefix, loremIpsum);
	t.log(loremIpsum);
	t.log(prefix, brokenLine);
	t.end();

	t.log(prefix, loremIpsum);

	t.begin();
	t.log(prefix, loremIpsum);

	t.begin();
	t.log(loremIpsum);
	t.log(prefix, loremIpsum);
	t.log(singleLine);

	t.end();
	t.end();
	t.log(prefix, loremIpsum);
}

function printDiffToErr(expected, found) {
	var diff = differ.diffChars(expected, found);
	diff.forEach(function(part){
				var color = part.added ? 'green' :
					part.removed ? 'red' : 'grey';
				var output = part.value;

				if (output.trim() === '') {
					output = output.replace('\r', '<CRETURN>');
					output = output.replace('\n', '<NEWLINE>');
					output = output.replace(' ', '<SPACE>');
					output = output.replace('\t', '<TAB>');
				}

				process.stderr.write(output[color]);
			});
}

describe('log-formatter', function() {
	before(function() {
		var oldLog = console.log;
		console.log = log;
		lf = require('../index.js');
		console.log = oldLog;
	});
	beforeEach(function() {
		resetLog();
	});
	describe('default', function() {
		it('output matches golden4indent.txt', function() {
			doStandardSequence(lf);

			if (output !== golden4Indent) {
				printDiffToErr(golden4Indent, output);
				throw new Error('Output did not match golden file.');
			}
		});
	});
	describe('with options', function() {
		it('output matches golden3indent70wrap.txt', function() {
			doStandardSequence(lf({
						indent: 3,
						out: log,
						lineLength: 70
					}));

			if (output !== golden3Indent70wrap) {
				printDiffToErr(golden3Indent70wrap, output);
				throw new Error('Output did not match golden file.');
			}
		});
	});
});
