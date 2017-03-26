/*
  This is the knowledgebase.
  Requests should be of the format:

  {
  'type': 'table' | 'query' | 'rule' | 'delete-row' | 'delete-col',
  'text': ...,
  'tableUpdate': { 'row': ..., 'col': ..., 'value': ...}
  }

  { 'index': ..., 'value': ... }
*/

const known = require('@shieldsbetter/known');
const k = known.factory;

const sexp = require('s-expression');

const nlp = require('compromise');

const fs = require('fs');
const path = require('path');
const uuidV4 = require('uuid/v4');

const express = require('express');
const bodyParser = require('body-parser');
const app = express();


// For display purposes, remember that facts are held as AEV
let db = [];
let attrs = {};
let rules = {};
let entities = {};

let queries = [
    // Unification rules
    '(#Noun|#Gerund|#Value|#Acronym) #Copula (#Noun|#Gerund|#Value|#Acronym) #Prepositon (#Noun|#Gerund|#Value|#Acronym)',
    '(#Noun|#Gerund|#Value|#Acronym) #Preposition (#Noun|#Gerund|#Value|#Acronym) #Copula (#Value|#Noun|#Gerund|#Acronym)',
    '#Copula (#Noun|#Gerund|#Value|#Acronym) (#Noun|#Gerund|#Value|#Acronym) (#Noun|#Gerund|#Value|#Acronym)',
    '#Copula (#Noun|#Gerund|#Value|#Acronym) #Preposition (#Noun|#Gerund|#Value|#Acronym) (#Noun|#Gerund|#Value|#Acronym)',
    '(#Noun|#Gerund|#Value|#Acronym) (#Noun|#Gerund|#Value|#Acronym) #Copula (#Noun|#Gerund|#Value|#Acronym)',
    // Question rules
    '(#Noun|#Gerund|#Value|#Acronym) #Preposition (#Noun|#Gerund|#Value|#Acronym)',
    '(#Noun|#Gerund|#Value|#Acronym) (#Noun|#Gerund|#Value|#Acronym)',
];

const varize = (title, term) => {
    return term.map((exp) => {
        if (exp[0].toUpperCase() === exp[0]) {
            return k.placeholder(title+'-'+exp);
        } else {
            return exp;
        }
    });
};

const addRule = (title, buf, flag) => {
    if (flag == 'sexp' || flag === undefined) {
        console.log("S-Expression");
        const terms = buf.split("\n").map((buf) => sexp(buf));
        console.log(terms);
        let expers = terms.map((term) => {
            const newterm = varize(title, term);

            if (term[0] == 'and' || term[0] == 'or') {
                const rest = newterm.slice(1).map((x) => varize(title, x));
                return k[term[0]](...rest);
            } else {
                return newterm;
            }
        });
        console.log(expers);
        db.push(k.implies(
            ...expers
        ));
        return expers;
    } else if (flag === 'natural') {
        console.log("Natural language");
        let rules = [];
        const lines = buf.split(/\n/);
        lines.forEach((line) => {
            console.log(line);
            queries.find((ms, matchingRule) => {
                const match = nlp(line).match(ms);
                if (match.found) {
                    console.log("Statement matched: " + ms);
                    let p = parseToAEV(match.terms(), matchingRule);
                    rules.push(p);
                    return true;
                }
                return false;
            });
        });

        db.push(k.implies(...rules));
        return rules;
    }
    return false;
};

const parseToAEV = (terms, matchingRule) => {
    let attribute, entity, value;
    let dat = terms.data().filter(d => d.normal !== '');

    if (matchingRule == 0) {
        [value, attribute, entity] = dat;
    } else if (matchingRule == 1) {
        [attribute,, entity,, value] = dat;
    } else if (matchingRule == 2) {
        [, attribute, entity, value] = dat;
    } else if (matchingRule == 3) {
        [, entity,, attribute, value] = dat;
    } else if (matchingRule == 4) {
        [entity, attribute,, value] = dat;
    } else if (matchingRule == 5) {
        [attribute,, entity] = dat;
    } else if (matchingRule == 6) {
        [entity, attribute] = dat;
    }

    return [attribute, entity, value].map((v) => {
        if (v === undefined) {
            return k.placeholder("QuestionVariable-"+uuidV4());
        } else if (v.bestTag === 'TitleCase' || v.bestTag === 'Acronym'
                   || v.text[0] == v.text[0].toUpperCase()) {
            return k.placeholder(v.normal.replace(/'[a-z]/g, ""));
        } else {
            return v.normal.replace(/'[a-z]/g, "");
        }
    });
};

const satisfyQuery = (terms, matchingRule) => {
    let request = parseToAEV(terms, matchingRule);
    return known.findValuations(request, known.dbize(db));
};

// Handle requests
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
    extended: true
}));
app.post('/', (req, res) => {
    var data = req.body;
    switch (data.type) {
    case 'reload':
        res.send({
            success: true,
            updated: null,
            data: {
                database: db.filter((d) => Array.isArray(d)),
                attrOrder: attrs,
                entityOrder: entities
            }
        });
        break;
    case 'table':
        const [a, e, v] = [data.tableUpdate.col.value || data.tableUpdate.col,
                           data.tableUpdate.row.value || data.tableUpdate.row,
                           data.tableUpdate.value];

        // Keep track
        if (data.tableUpdate.col.index) {
            attrs[a] = data.tableUpdate.col.index;
            entities[e] = data.tableUpdate.row.index;
        }

        if (typeof a !== 'string' || typeof e !== 'string' || typeof v !== 'string' ||
            a === '' || e === '' || v === '') {
            res.send({
                success: false,
                updated: 'database',
                data: 'Expecting valid Attributes, Entities, and Values'
            });
            return;
        }
        let alreadyPresent = false;
        db.forEach((el, i, db) => {
            if (a == el[0] && e == el[1]) {
                db[i] = [a, e, v];
                alreadyPresent = true;
            }
        });
        if (!alreadyPresent) {
            db.push([a, e, v]);
        }

        res.send({
            success: true,
            updated: 'database',
            data: {
                database: db.filter((d) => Array.isArray(d)),
                attrOrder: attrs,
                entityOrder: entities
            }
        });
        break;

    case 'delete-row':
        const row = data.tableUpdate.row;
        if (typeof row !== "string") {
            res.send({
                success: false,
                updated: 'database',
                data: 'Expecting a valid row.'
            });
            return;
        }
        delete entities[data.tableUpdate.row];
        db = db.filter((el) => {
            return el[1] !== row;
        });
        res.send({
            success: true,
            updated: 'database',
            data: {
                database: db.filter((d) => Array.isArray(d)),
                attrOrder: attrs,
                entityOrder: entities
            }
        });
        break;

    case 'delete-col':
        const col = data.tableUpdate.col;
        if (typeof col !== "string") {
            res.send({
                success: false,
                updated: 'database',
                data: 'Expecting a valid column.'
            });
            return;
        }
        delete attrs[data.tableUpdate.col];
        db = db.filter((el) => {
            return el[0] !== col;
        });
        res.send({
            success: true,
            updated: 'database',
            data: {
                database: db.filter((d) => Array.isArray(d)),
                attrOrder: attrs,
                entityOrder: entities
            }
        });
        break;

    case 'query':
        let foundQuery = null;
        console.log(data.text);

        queries.find((ms, i) => {
            console.log("Testing format " + i + ": " + ms);
            let match = nlp(data.text).match(ms);
            if (match.found) {
                console.log("Sentence matched!");
                foundQuery = satisfyQuery(match.terms(), i);
                console.log("Result is: " + foundQuery);
                return true;
            }
            return false;
        });

        res.send({
            success: !!foundQuery,
            updated: 'query-engine',
            data: foundQuery
        });
        break;

    case 'rule':
        const successful = addRule(data.title, data.text, data.flag);
        rules[data.title] = data;

        res.send({
            success: !!successful,
            updated: 'rules',
            data: successful
        });
        break;

    case 'rules':
        res.send({
            success: true,
            updated: null,
            data: rules
        });
        break;

    default:
        res.send({
            success: false,
            updated: null,
            data: 'Unknown command.'
        });
    }
});

// Serve files
var options = {
    dotfiles: 'ignore',
    etag: true,
    extensions: ['htm', 'html', 'jpg', 'png'],
    index: 'index.html',
    lastModified: true,
    maxAge: '1d',
    setHeaders: function (res, path, stat) {
        res.set('x-timestamp', Date.now());
        res.header('Cache-Control', 'public, max-age=1d');
    }
};
app.use(express.static(path.join(__dirname, 'public/'), options));

app.listen(3000, function () {
    console.log('AtomicDatabase bombing you on port http://localhost:3000!');
});
