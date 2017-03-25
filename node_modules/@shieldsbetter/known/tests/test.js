var assert = require('assert');
var deepEqual = require('deep-equal');

var m = require('../index');
var testCases = require('./testCases');

var exitCode = 0;

testCases.forEach(function(tc, index) {
	assert(tc.name, 'Test case ' + index + ' must have name.');

	var passed = true;
	console.log('>>> ' + tc.name);

	var valuations = m.findValuations(tc.querySchema, m.dbize(tc.db));

	var foundIndices = {};
	valuations.forEach(function(found) {
		var matches = false;
		
		tc.expectedBindings.forEach(function(expected, expectedIndex) {
			if (!matches && !foundIndices[expectedIndex] &&
					deepEqual(found, expected, {strict: true})) {
				matches = true;
				foundIndices[expectedIndex] = true;
			}
		});

		if (!matches) {
			passed = false;
			console.log('  Unexpected binding: ' + JSON.stringify(found));
		}
	});

	Object.getOwnPropertyNames(foundIndices).forEach(function(found) {
		tc.expectedBindings[found] = false;
	});

	tc.expectedBindings.forEach(function(expected, expectedIndex) {
		if (expected) {
			passed = false;
			console.log('  Expected binding #' + expectedIndex +
					' not found.  Wanted: ' + JSON.stringify(expected) +
					'\n    Found these: ' + JSON.stringify(valuations));
		}
	});

	if (passed) {
		console.log("  Passed.");
	}
	else {
		exitCode = 1;
	}

	console.log();
});

process.exit(exitCode);
