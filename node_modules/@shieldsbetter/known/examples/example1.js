var known = require('../index');
var kfac = known.factory;

var db = [
	['is-dog', 'scout'],
    ['is-dog', 'hunter'],
	['is-dog', 'bandit'],
	['likes-fetch', 'scout'],
	['is-senior', 'hunter'],
	kfac.implies(
		kfac.and(
			['is-dog', kfac.placeholder('x')],
			['likes-fetch', kfac.placeholder('x')]),
		['will-fetch', kfac.placeholder('x'), 'stick'],
		['gets-enough-exercise', kfac.placeholder('x')])
];

var valuations = known.findValuations(
		kfac.or(
			['gets-enough-exercise', kfac.placeholder('x')],
			['is-senior', kfac.placeholder('x')]),
		known.dbize(db));

console.log(valuations);
