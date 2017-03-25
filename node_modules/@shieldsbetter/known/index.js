var clone = require('clone');
var logFormatter = require('@shieldsbetter/log-formatter');

var factory = require('./factory');

var debugOn = false;

var debugBegin = function() { };
var debug = function() { };
var debugEnd = function() { };

function callOrUndefined(f) {
	var result;

	if (!f) {
		result = undefined;
	}
	else if (typeof f === 'function') {
		result = f();
	}
	else {
		result = f;
	}

	return result;
}

if (debugOn) {
	debugBegin = function(s1, s2) {
		logFormatter.begin();
		if (s1) {
			logFormatter.log(callOrUndefined(s1), callOrUndefined(s2));
		}
	}

	debug = function(s1, s2) {
		logFormatter.log(callOrUndefined(s1), callOrUndefined(s2));
	}

	debugEnd = function(s1, s2) {
		if (s1) {
			logFormatter.log(callOrUndefined(s1), callOrUndefined(s2));
		}

		logFormatter.end();
	}
}

function instantiateBinder(binder, bindings) {
	if (typeof binder === 'string') {
		return binder;
	}

	if (Array.isArray(binder)) {
		var result = [];
		binder.forEach(function(element) {
			result.push(instantiateBinder(element, bindings));
		});
		return result;
	}

	if (bindings[binder.name]) {
		return bindings[binder.name];
	}

	return binder;
}

function instantiateSchema(schema, bindings) {
	debugBegin('instantiateSchema: ', function() {
		return JSON.stringify(schema) + '\n' + JSON.stringify(bindings);
	});

	var result;

	if (!Array.isArray(schema) && typeof schema === 'object') {
		var expressions = [];
		schema.expressions.forEach(function(subschema) {
			expressions.push(instantiateSchema(subschema, bindings));
		});

		result = {
			op: schema.op,
			expressions: expressions
		};
	}
	else {
		result = instantiateBinder(schema, bindings);
	}

	debugEnd('Result: ', function() {
		return JSON.stringify(result);
	});
	return result;
}

function getFreeVariables(binder, bindings) {
	var accum = [];
	buildFreeVariables(binder, bindings, accum);
	return accum;
}

function buildFreeVariables(binder, bindings, accum) {
	if (typeof binder === 'string') {
		return;
	}

	if (Array.isArray(binder)) {
		for (var i = 0; i < binder.length; i++) {
			buildFreeVariables(binder[i], bindings, accum);
		}
		return;
	}

	if (!bindings[binder.name]) {
		accum.push(binder.name);
	}
}

/*
 * Binds 'instantiatedBinder' against 'expression', adding any newly-bound
 * variables to the bindings object.  If binding is successful, returns true and
 * bindings will reflect the final binding of all free variables.  If binding is
 * unsuccessful, returns false and the bindings object will be left in an
 * undefined state.
 */
function bindExp(instantiatedBinder, expression, bindings) {
	debugBegin('bindExp: ', function() {
		return JSON.stringify(instantiatedBinder) + '\n' +
				JSON.stringify(expression) + '\n' + JSON.stringify(bindings);
	});

	var result;

	if (typeof instantiatedBinder === 'string') {
		result = (typeof expression === 'string')
				&& instantiatedBinder === expression;
	}
	else if (Array.isArray(instantiatedBinder)) {
		if (!Array.isArray(expression) ||
					instantiatedBinder.length !== expression.length) {
			result = false;
		}
		else {
			var matching = true;
			var subIndex = 0;
			while (matching && subIndex < expression.length) {
				matching = bindExp(instantiatedBinder[subIndex],
						expression[subIndex], bindings);
				subIndex++;
			}

			result = matching;
		}
	}
	else {
		bindings[instantiatedBinder.name] = expression;
		result = true;
	}

	debugEnd('Result: ', function() {
		return result + ', ' + JSON.stringify(bindings);
	});
	return result;
}

function findImplicationValuations(
			instantiatedBinder, implication, bindings, db) {
	debugBegin('findImplicationValuations', function() {
		return JSON.stringify(instantiatedBinder) + '\n' +
				JSON.stringify(implication) + '\n' + JSON.stringify(bindings);
	});

	var binderFreeVars = getFreeVariables(instantiatedBinder, bindings);

	debug('freevars: ', function() {
		return JSON.stringify(binderFreeVars);
	});

	var potentialConclusions = implication.conclude;
	var givenSchema = implication.given;

	var valuations = [];
	for (var i = 0; i < potentialConclusions.length; i++) {
		var conclusion = potentialConclusions[i];

		// Does this conclusion look like what we want to conclude?
		var conclusionBindings = {};
		if (bindExp(conclusion, instantiatedBinder, conclusionBindings)) {

			debug('conclusion-to-binder-map:', function() {
				return JSON.stringify(conclusionBindings);
			});

			// Yes it does!
			// Let's see if there's any way to valuate the requirements.
			var givenValuations =
					 findValuations(givenSchema, db, conclusionBindings);

			for (var j = 0; j < givenValuations.length; j++) {
				// We may have bound some stuff we don't care about.
				var valuation = {};

				var fullyBound = true;
				binderFreeVars.forEach(function(freeVar) {
					var freeVarVal = givenValuations[j][freeVar];

					if (freeVarVal) {
						valuation[freeVar] = freeVarVal;
					}
					else {
						fullyBound = false;
					}
				});

				if (fullyBound) {
					valuations.push(valuation);
				}
			}
		}
	}	

	debugEnd('Result: ', function() {
		return JSON.stringify(valuations)
	});
	return valuations;
}

function arrLast(arr) {
	return arr[arr.length - 1];
}

/*
 * Takes a query schema, a database, and some pre-existing bindings and returns
 * an array of valuations of free variables within the given schema.  Each
 * valuation is sufficient to satisfy the schema against the database.  If the
 * schema is not satisfiable against the database, returns the empty array.
 * Databases are permitted to contain identical facts and resulting identical
 * bindings are not pruned.
 *
 * Regardless of outcome, the input bindings will remain unchanged.
 */
function findValuations(schema, db, bindings) {
	debugBegin('findValuations: ', function() {
		return JSON.stringify(schema) + '\n\n' + JSON.stringify(bindings);
	});
	schema = instantiateSchema(schema, bindings);

	var result;
	if (Array.isArray(schema) || typeof schema === 'string') {
		var candidateFacts = db.getCandidateFacts(schema);
		var valuations = [];
		while (candidateFacts.hasNext()) {
			var fact = candidateFacts.next();
			
			if (Array.isArray(fact) || typeof fact === 'string') {
				var tmpBindings = clone(bindings);
				if (bindExp(schema, fact, tmpBindings)) {
					valuations.push(tmpBindings);
				}
			}
			else {
				if (fact.op !== 'implies') {
					throw new Error();
				}

				var subValuations =
						findImplicationValuations(schema, fact, bindings, db);
				for (var j = 0; j < subValuations.length; j++) {
					valuations.push(subValuations[j]);
				}
			}
		}

		result = valuations;
	}
	else if (schema.op === 'and') {
		var valuations = [];
		var tmpVals =
				[findValuations(schema.expressions[0], db, bindings)];

		while (tmpVals.length > 0) {
			if (arrLast(tmpVals).length > 0) {
				if (tmpVals.length == schema.expressions.length) {
					valuations.push(arrLast(arrLast(tmpVals)));
					arrLast(tmpVals).pop();
				}
				else {
					tmpVals.push(findValuations(
							schema.expressions[tmpVals.length], db,
							arrLast(arrLast(tmpVals))));
				}
			}
			else {
				tmpVals.pop();

				if (tmpVals.length > 0) {
					arrLast(tmpVals).pop();
				}
			}
		}

		result = valuations;
	}
	else if (schema.op === 'or') {
		var valuations = [];

		for (var i = 0; i < schema.expressions.length; i++) {
			var subBindings =
					findValuations(schema.expressions[i], db, bindings);
			for (var j = 0; j < subBindings.length; j++) {
				valuations.push(subBindings[j]);
			}
		}

		result = valuations;
	}
	else {
		throw new Error();
	}
	
	debugEnd('Result: ', function() {
		return JSON.stringify(valuations)
	});
	return result
}

function dbize(arr) {
	return {
		getCandidateFacts: function(schema) {
			var index = 0;
			return {
				hasNext: function() {
					return index < arr.length;
				},
				next: function() {
					var result = arr[index];
					index++;
					return result;
				}
			};
		}
	};
}

module.exports = {
	findValuations:
			function(schema, db) { return findValuations(schema, db, {}); },
	dbize: dbize,
	factory: factory
};
