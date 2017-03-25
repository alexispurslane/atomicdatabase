@shieldsbetter/known
====================

A template-satisfying query engine for node in the style of Prolog.

Matches a template query against a database of known facts and implications to produce a set of free-variable bindings that satisfy the query.

Current version is functional but implemented naively.

Usage
-----

```javascript
var known = require('@shieldsbetter/known');
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
```

Output:

```javascript
[ { x: 'scout' }, { x: 'hunter' } ]
```

Glossary
--------
Many known terms have a hierarchal relationship expressed here.  Terms in sub-bullets are sub-types of the term defined in their parent bullets.

* **expression** - An indication of relationship, possibly containing placeholders.
	* **schema** - An acceptable query template, possibly containing placeholders.
		* **simple schema** - a schema without a top-level logical operator.
			* **terminal** - a string indicating the relationship of itself with truth.  `'is-raining'` is a terminal indicating, 'it is true that it is raining.'
			* **placeholder** - a placeholder accepting any single relationship.  `known.factory.placeholder('x')` is a placeholder indicating 'any relationship is acceptable, unless *x* has already been bound in this context, in which case only the previously-bound relationship is acceptable.'
			* **relation** - an array of simple schemas indicating a relationship between the elements of the array.  `[['is-raining', 'is-snowing'], 'called', known.factory.placeholder('x')]` is a relation indicating 'the three elements of this array have an understood relationship'.
		* **compound schema** - a value derived from the `known.factory` api representing an *and* or *or* relationship amongst schemas.
	* **implication** - An expression derived from `known.factory.implies()` indicating an 'in order to valuate schemas *x*, *y*, or *z* it would be sufficient to valuate schema *a*' relationship.  In all cases, *a* must bind all placeholders introduced by the schema the engine seeks to establish or an error will occur.  ``known.factory.implies(known.factory.and(['foo', known.factory.placeholder('x')], ['bar', known.factory.placeholder('x')]), ['bizz', known.factory.placeholder('x')], ['bazz', known.factory.placeholder('x')])`` is a relationship indicating that, were the engine to need to valuate `['bizz', known.factory.placeholder('x')]` or `['bazz', known.factory.placeholder('x')]`, it would be sufficient to find a valuation for `x` satisfying both `['foo', known.factory.placeholder('x')]` and `['bar', known.factory.placeholder('x')]`.

In addition to this hierarchy, a schema is considerd **bound** if it contains zero placeholders (inductively including any sub-schemas), and a **fact** is any implication or bound simple schema.


known api
---------
* **dbize(** *array* **)** - converts an array of facts into a database suitable for known's use.
* **factory** - an object containing constructors for implications, compound schemas, and placeholders.
	* **and(** *conjunct1*, *conjunct2*, ... *conjunctN* **)** - builds an *and* compound schema.  Each conjunct must itself be a schema.  Matching valuations must satisfy each conjunct.
	* **or(** *disjunct1*, *disjunct2*, ... *disjunctN* **)** - builds an *or* compound scehma.  Each disjunct must itself be a schema.  Matching valuations must satisfy at least one conjunct.
	* **placeholder(** *name* **)** - builds a placeholder schema.  Binds against any sub-expression, but identically-named placeholders must bind against identical sub-expressions.
	* **implies(** *given*, *conclusion1*, *conclusion2*, ... *conclusionN* **)** - builds an implication expression.  When attempting to valuate a simple schema that matches one of the conclusion schemas, the engine will accept valuations for the (possibly compound) *given* schema instead.
* **findValuations(** *schema*, *database* **)** - returns an array of valuations that satisfy the given query schema against the given database.  Each valuation will be an object that maps the names of placeholders in *schema* to bound sub-expressions from *database* such that, were the placeholders in *schema* to be replaced with their corresponding sub-expressions, the schema would represent a true statement based on available facts in the database.  There may be multiple such valuations.  If no such valuations exist, returns an empty array.  If the given query schema does not contain any placeholders (i.e., is *bound*), but is supported by the database, returns one or more empty valuations.  Databases are permitted to contain redundant facts, which may lead to redundant valuations.  The given database may be any value that conforms to the *database interface*, such as a value returned by **known.dbize()**.

database interface
------------------
Databases must implement a single method:
* **getCandidateFacts(** *schema* **)** - returns a value conforming to the *iterator interface* that iterates over all facts in the database that might potentially match the given simple schema.  The database may return spurious facts, but must not exclude any facts that would match.  A naive database may simply return all its facts.

iterator interface
------------------
Iterators must implement the following methods:
* **hasNext()** - returns *true* if and only if another value exists in the iteration.
* **next()** - returns the next value in the iteration.  If there are no further values, the behavior of this method is undefined.
