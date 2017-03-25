module.exports = {
	and: function() {
		var expressions = Array.prototype.slice.call(arguments).slice();

		return {
			op: 'and',
			expressions: expressions
		};
	},
	or: function() {
		var expressions = Array.prototype.slice.call(arguments).slice();

		return {
			op: 'or',
			expressions: expressions
		};
	},
	placeholder: function(name) {
		return {
			op: 'ph',
			name: name
		};
	},
	implies: function(antecedent) {
		return {
			op: 'implies',
			given: antecedent,
			conclude: Array.prototype.slice.call(arguments).slice(1)
		};
	}
};
