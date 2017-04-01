const known = require('@shieldsbetter/known');
const k = known.factory;
const parseSexp = require('s-expression');
const fs = require('fs');
const nlp = require('compromise');
const uuidV4 = require('uuid/v4');

// For display purposes, remember that facts are held as AEV

////////////////////// DATABASE INTERFACE
let db = [];
let attrs = {};
let rules = {};
let entities = {};
let filename;

module.exports.loadDatabase = (f) => {
    filename = f;
    console.log("Loading database at " + f + "...");
    let file = fs.readFileSync(f, "utf8");
    if (file.trim() !== '') {
        let data = JSON.parse(file);
        if (data.db && data.attrs && data.rules && data.entities) {
            db = data.db;
            attrs = data.attrs;
            rules = data.rules;
            entities = data.entities;
        }
    }
};

module.exports.getRules = () => rules;

module.exports.updateDatabase = (a, e, v, colIndex, rowIndex) => {
    if (colIndex !== undefined) attrs[a] = colIndex;
    if (rowIndex !== undefined) entities[e] = rowIndex;

    let alreadyPresent = false;
    db.forEach((el, i, db) => {
        if (a === el[0] && e === el[1]) {
            db[i] = [a, e, v];
            alreadyPresent = true;
        }
    });
    if (!alreadyPresent) {
        db.push([a, e, v]);
    }
};

module.exports.saveDatabase = (f=filename) => {
    console.log("Saving database to " + f + "...");
    const data = {
        db: db,
        attrs: attrs,
        entities: entities,
        rules: rules
    };
    fs.writeFileSync(f, JSON.stringify(data));
};

module.exports.deleteCol = (col) => {
    delete attrs[col];
    db = db.filter((el) => {
        return el[0] !== col;
    });
};

module.exports.deleteRow = (row) => {
    delete entities[row];
    db = db.filter((el) => {
        return el[1] !== row;
    });
};

module.exports.deleteRule = (title) => {
    let indb = title in rules;
    if (indb) {
        delete db[rules[title].index];
        delete rules[title];
    }

    return indb;
};

module.exports.rememberRule = (rule, data) => {
    data.index = db.length - 1;
    rules[data.title] = data;
};

module.exports.safeDB = () => {
    return [db.filter(d => Array.isArray(d)), attrs, entities];
};

////////////////////// PARSING
let queries = [
    // Unification rules
    '(#Noun|#Gerund|#Adjective|#Value|#Acronym) #Copula (#Noun|#Gerund|#Adjective|#Value|#Acronym) #Prepositon (#Noun|#Gerund|#Adjective|#Value|#Acronym)',
    '(#Noun|#Gerund|#Adjective|#Value|#Acronym) #Preposition (#Noun|#Gerund|#Adjective|#Value|#Acronym) #Copula (#Value|#Noun|#Gerund|#Adjective|#Acronym)',
    '#Copula (#Noun|#Gerund|#Adjective|#Value|#Acronym) (#Noun|#Gerund|#Adjective|#Value|#Acronym) (#Noun|#Gerund|#Adjective|#Value|#Acronym)',
    '#Copula (#Noun|#Gerund|#Adjective|#Value|#Acronym) #Preposition (#Noun|#Gerund|#Adjective|#Value|#Acronym) (#Noun|#Gerund|#Adjective|#Value|#Acronym)',
    '(#Noun|#Gerund|#Adjective|#Value|#Acronym) (#Noun|#Gerund|#Adjective|#Value|#Acronym) #Copula (#Noun|#Gerund|#Adjective|#Value|#Acronym)',
    // Question rules
    '(#Noun|#Gerund|#Adjective|#Value|#Acronym) #Preposition (#Noun|#Gerund|#Adjective|#Value|#Acronym)',
    '(#Noun|#Gerund|#Adjective|#Value|#Acronym) (#Noun|#Gerund|#Adjective|#Value|#Acronym)',
];

const splitByConj = (line) => {
    const conj = nlp(line).terms().data().find(
        x => x.tags.indexOf('Conjunction') !== -1);
    if (conj !== undefined) {
        console.log("Conjunction found!");
        let loc = line.indexOf(conj.normal);
        let size = conj.normal.length+1;

        let car = line.substring(0, loc-1);
        let cdr = line.substring(loc+size);
        return k[conj.normal](parseFullyToAEV(car), splitByConj(cdr));
    } else {
        return parseFullyToAEV(line);
    }
};

const parseExpers = (title, sexp) => {
    console.log(sexp);
    if (Array.isArray(sexp)) {
        if (sexp[0] === "and" || sexp[0] === "or") {
            return k[sexp[0]](...sexp.slice(1).map((x) => parseExpers(title, x)));
        } else {
            return sexp.map((x) => parseExpers(title, x));
        }
    } else {
        if (sexp === sexp.toUpperCase() && isNaN(sexp)) {
            return k.placeholder(title+"-"+sexp.toLowerCase());
        } else if (sexp === undefined) {
            return k.placeholder(title+"-"+uuidV4());
        } else {
            return sexp;
        }
    }
};

const allCompleteSexps = (buffer) => {
    let parens = 0;
    let sexps = [];
    let sexp = '';
    buffer.split('').forEach((char) => {
        if (char === '(') parens++;
        if (char === ')') parens--;
        if (parens > 0 || char.replace(/\s+/, "") !== "") sexp += char;
        if (parens === 0 && sexp !== "") { sexps.push(sexp); sexp = ""; }
    });

    return sexps.map(parseSexp);
};

const prepare = x => x.replace(/#.*$/gi, '').replace(/[{\[<]/gi, '(').replace(/[}\]>]/gi, ')');

const parseFullyToAEV = (line) => {
    let found = false;
    return queries.map((ms, matchingRule) => {
        const match = nlp(line).match(ms);
        if (match.found && !found) {
            console.log("Sentence matched rule " +matchingRule+": " + ms);
            found = true;
            return parseToAEV(match.terms(), matchingRule);
        }
        return undefined;
    }).filter(x => x !== undefined)[0];
};

const parseToAEV = (terms, matchingRule) => {
    let attribute, entity, value;
    let dat = terms.data().filter(d => d.normal !== '');

    if (matchingRule === 0) {
        [value, attribute, entity] = dat;
    } else if (matchingRule === 1) {
        [attribute,, entity,, value] = dat;
    } else if (matchingRule === 2) {
        [, attribute, entity, value] = dat;
    } else if (matchingRule === 3) {
        [, entity,, attribute, value] = dat;
    } else if (matchingRule === 4) {
        [entity, attribute,, value] = dat;
    } else if (matchingRule === 5) {
        [attribute,, entity] = dat;
    } else if (matchingRule === 6) {
        [entity, attribute] = dat;
    }

    return [attribute, entity, value].map(v => {
        if (v === undefined) {
            return k.placeholder(entity.normal+"-"+attribute.normal);
        }

        let vt = v.text.replace(/'[a-z]/g, "");
        if (vt === vt.toUpperCase() && isNaN(v.text)) {
            return k.placeholder(v.normal.replace(/'[a-z]/g, ""));
        } else {
            return v.normal.replace(/'[a-z]/g, "");
        }
    });
};

////////////////////// KNOWLEDGEBASE INTERFACE
module.exports.isUnderstood = (exp) => {
    if (Array.isArray(exp)) {
        return exp.every(module.exports.isUnderstood);
    } else {
        return !!exp;
    }
};
module.exports.satisfyQuery = (line) => {
    let s = splitByConj(line);
    if (s) {
        return known.findValuations(s, known.dbize(db));
    } else {
        return null;
    }
};

module.exports.addRule = (title, buf, flag) => {
    console.log();
    console.log("Rule: " + title);
    console.log("Format: " + flag);
    console.log("Text: " + buf);
    console.log();
    let res = false;
    if (flag === 'sexp' || flag === undefined) {
        console.log("S-Expression");
        const exprs = parseExpers(title, allCompleteSexps(prepare(buf)));
        res = k.implies(...exprs);
        db.push(res);
    } else if (flag === 'natural') {
        console.log("Natural language");
        res = [];
        const lines = nlp(buf).statements().data().map(x => x.text);
        console.log(lines);
        lines.forEach((line) => {
            res.push(splitByConj(line));
        });

        db.push(k.implies(...res));
    }

    module.exports.saveDatabase();
    return res;
};
