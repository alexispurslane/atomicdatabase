const known = require("@shieldsbetter/known");
const kfac = known.factory;

var db = [
    ['father', 'tom', 'barry'],
    ['father', 'barry', 'joe'],
    kfac.implies(
        kfac.and(['father', kfac.placeholder('x'), kfac.placeholder('y')],
                 ['father', kfac.placeholder('y'), kfac.placeholder('z')]),
        ['grandfather', kfac.placeholder('x'), kfac.placeholder('z')]
    )
];

console.log(known.findValuations(['grandfather', 'tom', kfac.placeholder('person')],
                                 known.dbize(db)));
