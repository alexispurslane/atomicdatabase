var linewrap = require('linewrap');
var merge = require('merge');

var defaultOptions = {
			indent: 4,
			out: console.log,
			lineLength: 80
		};

function installFormatterMethods(t, options) {
	if (!options) {
		options = {};
	}

	options = merge(defaultOptions, options);

	var indentLevel = 0;

	t.log = function(s1, s2) {
		var prefix, msg;

		if (s2) {
			prefix = s1;
			msg = s2;
		}
		else {
			prefix = '';
			msg = s1;
		}

		var originalLines = msg.split(/\r?\n/);

		var wrap = linewrap(indentLevel * options.indent, options.lineLength,
				{mode: 'hard', wrapLineIndent: prefix.length});
		var first = true;
		originalLines.forEach(function(line) {
					if (first) {
						var val = wrap(prefix + line);
						options.out(wrap(prefix + line));
						first = false;
						wrap = linewrap(
								indentLevel * options.indent + prefix.length,
								options.lineLength, {mode: 'hard'});
					}
					else {
						options.out(wrap(line));
					}
				});
	};

	t.begin = function() {
		indentLevel++;
	};
	
	t.end = function() {
		indentLevel--;
	};

	return t;
}

if (typeof module !== 'undefined') {
	var root = function(options) {
		return installFormatterMethods({}, options);
	};
	installFormatterMethods(root);

	module.exports = root;
}
