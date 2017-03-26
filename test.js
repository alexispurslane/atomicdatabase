const known = require("@shieldsbetter/known");
const kfac = known.factory;

var db = [
    ['father', 'tom', 'barry'],
    ['father', 'barry', 'joe'],
    ['father', 'tim', 'joe'],
    kfac.implies(
        kfac.and(['father', kfac.placeholder('a'), kfac.placeholder('f')],
                 ['father', kfac.placeholder('b'), kfac.placeholder('f')]),
        ['sibling', kfac.placeholder('a'), kfac.placeholder('b')]
    )
];

console.log(known.findValuations(['sibling', 'barry', kfac.placeholder('person')],
                                 known.dbize(db)));
