var assert = require('assert');
var linewrap = require('../');

exports.invalidvalues = function() {
    var optionMap = {
        'preset': 'invalid preset',
        'mode': 'invalid mode',
        'whitespace': 'invalid whitespace',
        'skip': 100,
        'skipScheme': 'invalid scheme',
        'lineBreak': {},
        'lineBreakScheme': 'invalid scheme',
        'respectLineBreaks': 'invalid',
        'tabWidth': [],
        'preservedLineIndent': 'invalid',
        'wrapLineIndent': -1
    };
    var options = Object.keys(optionMap),
        option, error;

    for (var i = 0; i < options.length; i++) {
        error = null;
        option = {};
        option[options[i]] = optionMap[options[i]];
        try {
            linewrap(30, option);
        } catch (e) {
            error = e;
        }

        assert.ok(error instanceof TypeError);
        assert.equal(error.message.indexOf(options[i] + ' must be '), 0);
    }
};
