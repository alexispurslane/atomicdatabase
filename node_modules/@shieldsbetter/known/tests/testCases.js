var mf = require('../factory');

module.exports = [
	{
		name: 'simple multi-match',
		db: [
			['is-dog', 'alex'],
			['color', 'sam', 'sable'],
			['color', 'alex', 'black'],
			['is-dog', 'sam']
		],
		querySchema: ['is-dog', mf.placeholder('x')],
		expectedBindings: [
			{ x: 'alex' }, { x: 'sam' }
		]
	},
	{
		name: 'simple cascading match w/ and',
		db: [
			['is-dog', 'alex'],
			['color', 'sam', 'sable'],
			['color', 'alex', 'black'],
			['is-dog', 'sam']
		],
		querySchema: mf.and(
			['is-dog', mf.placeholder('x')],
			['color', mf.placeholder('x'), 'black']
		),
		expectedBindings: [
			{ x: 'alex' }
		]
	},
	{
		name: 'match inductive list + or',
		db: [
			['color', 'sam', 'sable'],
			['knows-trick', 'kris', ['fetch', 'ball']],
			['is-dog', 'alex'],
			['is-dog', 'kris'],
			['is-dog', 'sam'],
			['is-impressive', ['fetch', 'ball']]
		],
		querySchema: mf.and(
			['is-dog', mf.placeholder('x')],
			mf.or(
				mf.and(
					['knows-trick', mf.placeholder('x'), mf.placeholder('y')],
					['is-impressive', mf.placeholder('y')]
				),
				['color', mf.placeholder('x'), 'sable']
			)
		),
		expectedBindings: [
			{ x: 'kris', y: ['fetch', 'ball'] }, { x: 'sam' }
		]
	},
	{
		name: 'basic implication - implication rule first',
		db: [
			mf.implies(
				['is-dog', mf.placeholder('x')],
				['likes-pets', mf.placeholder('x')]),
			['is-dog', 'sam'],
			['color', 'sam', 'sable'],
			['is-cat', 'Meow is the summer of our discatent']
		],
		querySchema: ['likes-pets', mf.placeholder('x')],
		expectedBindings: [
			{ x: 'sam' }
		]
	},
	{
		name: 'basic implication - implication rule second',
		db: [
			['is-dog', 'sam'],
			['color', 'sam', 'sable'],
			['is-cat', 'Meow is the summer of our discatent'],
			mf.implies(
				['is-dog', mf.placeholder('x')],
				['likes-pets', mf.placeholder('x')]),
		],
		querySchema: ['likes-pets', mf.placeholder('x')],
		expectedBindings: [
			{ x: 'sam' }
		]
	},
	{
		name: 'implication with multiple consequents -- matching first',
		db: [
			mf.implies(
				['is-dog', mf.placeholder('x')],
				['likes-pets', mf.placeholder('x')],
				['craves-peanut-butter', mf.placeholder('x')],
				['good-dog', mf.placeholder('x')]),
			['is-dog', 'sam'],
			['is-dog', 'alex'],
			['color', 'sam', 'sable'],
			['is-cat', 'Meow is the summer of our discatent']
		],
		querySchema: ['likes-pets', mf.placeholder('x')],
		expectedBindings: [
			{ x: 'sam' }, { x: 'alex' }
		]
	},
	{
		name: 'implication with multiple consequents -- matching middle',
		db: [
			mf.implies(
				['is-dog', mf.placeholder('x')],
				['craves-peanut-butter', mf.placeholder('x')],
				['likes-pets', mf.placeholder('x')],
				['good-dog', mf.placeholder('x')]),
			['is-dog', 'sam'],
			['is-dog', 'alex'],
			['color', 'sam', 'sable'],
			['is-cat', 'Meow is the summer of our discatent']
		],
		querySchema: ['likes-pets', mf.placeholder('x')],
		expectedBindings: [
			{ x: 'sam' }, { x: 'alex' }
		]
	},
	{
		name: 'implication with multiple consequents -- matching last',
		db: [
			mf.implies(
				['is-dog', mf.placeholder('x')],
				['craves-peanut-butter', mf.placeholder('x')],
				['good-dog', mf.placeholder('x')],
				['likes-pets', mf.placeholder('x')]),
			['is-dog', 'sam'],
			['is-dog', 'alex'],
			['color', 'sam', 'sable'],
			['is-cat', 'Meow is the summer of our discatent']
		],
		querySchema: ['likes-pets', mf.placeholder('x')],
		expectedBindings: [
			{ x: 'sam' }, { x: 'alex' }
		]
	},
	{
		name: 'implication with placeholder collision',
		db: [
			mf.implies(
				['is-dog', mf.placeholder('x')],
				['is-good-dog', mf.placeholder('x')]),
			['is-dog', 'pat']
		],
		querySchema: ['is-good-dog', mf.placeholder('x')],
		expectedBindings: [
			{ x: 'pat' }
		]
	},
	{
		name: 'implication with compound antecedent --- implication first',
		db: [
			mf.implies(
				mf.and(
					['is-dog', mf.placeholder('a')],
					mf.or(
						mf.and(
							['knows-trick', mf.placeholder('a'),
									mf.placeholder('b')],
							['is-impressive', mf.placeholder('b')]
						),

						// Old dogs can even impress with tricks they aren't
						// very good at or wouldn't otherwise be impressive!
						mf.and(
							['is-old', mf.placeholder('a')],
							['knows-trick', mf.placeholder('c'),
									mf.placeholder('b')]
						)
					)
				),
				['can-impress-with', mf.placeholder('a'), mf.placeholder('b')]),
			['color', 'sam', 'sable'],
			['knows-trick', 'sam', ['fetch', 'ball']],
			['knows-trick', 'sam', 'bark'],
			['knows-trick', 'kris', 'bark'],
			['knows-trick', 'alex', 'bark'],
			['is-dog', 'alex'],
			['is-dog', 'kris'],
			['color', 'kris', 'black'],
			['is-dog', 'sam'],
			['is-dog', 'pat'],
			['color', 'alex', 'sable'],
			['is-impressive', ['fetch', 'ball']],
			['is-impressive', 'shake'],
			['is-old', 'alex'],
			['is-cat', 'Meow is the summer of our discatent'],
			['knows-trick', 'Meow is the summer of our discatent', 'shake'],
		],
		querySchema: 
				['can-impress-with', mf.placeholder('x'), mf.placeholder('y')],
		expectedBindings: [
			{ x: 'sam', y: ['fetch', 'ball'] },
			{ x: 'alex', y: ['fetch', 'ball'] },
			{ x: 'alex', y: 'shake' },

			// Once because barking is a thing alex can do.
			{ x: 'alex', y: 'bark' },

			// Once because barking is a thing sam can do.
			{ x: 'alex', y: 'bark' },

			// Once because barking is a thing kris can do.
			{ x: 'alex', y: 'bark' },
		]
	},
	{
		name: 'implication with compound antecedent --- implication last',
		db: [
			['color', 'sam', 'sable'],
			['knows-trick', 'sam', ['fetch', 'ball']],
			['knows-trick', 'sam', 'bark'],
			['knows-trick', 'kris', 'bark'],
			['knows-trick', 'alex', 'bark'],
			['is-dog', 'alex'],
			['is-dog', 'kris'],
			['color', 'kris', 'black'],
			['is-dog', 'sam'],
			['is-dog', 'pat'],
			['color', 'alex', 'sable'],
			['is-impressive', ['fetch', 'ball']],
			['is-impressive', 'shake'],
			['is-old', 'alex'],
			['is-cat', 'Meow is the summer of our discatent'],
			['knows-trick', 'Meow is the summer of our discatent', 'shake'],
			mf.implies(
				mf.and(
					['is-dog', mf.placeholder('a')],
					mf.or(
						mf.and(
							['knows-trick', mf.placeholder('a'),
									mf.placeholder('b')],
							['is-impressive', mf.placeholder('b')]
						),

						// Old dogs can even impress with tricks they aren't
						// very good at or wouldn't otherwise be impressive!
						mf.and(
							['is-old', mf.placeholder('a')],
							['knows-trick', mf.placeholder('c'),
									mf.placeholder('b')]
						)
					)
				),
				['can-impress-with', mf.placeholder('a'), mf.placeholder('b')]),
		],
		querySchema: 
				['can-impress-with', mf.placeholder('x'), mf.placeholder('y')],
		expectedBindings: [
			{ x: 'sam', y: ['fetch', 'ball'] },
			{ x: 'alex', y: ['fetch', 'ball'] },
			{ x: 'alex', y: 'shake' },

			// Once because barking is a thing alex can do.
			{ x: 'alex', y: 'bark' },

			// Once because barking is a thing sam can do.
			{ x: 'alex', y: 'bark' },

			// Once because barking is a thing kris can do.
			{ x: 'alex', y: 'bark' },
		]
	},
];
