/*
  This is the knowledgebase.
  Requests should be of the format:

  {
  'type': 'table' | 'query' | 'rule' | 'delete-row' | 'delete-col',
  'text': ...,
  'tableUpdate': { 'row': ..., 'col': ..., 'value': ...}
  }
*/

const known = require('@shieldsbetter/known');
const k = known.kfac;

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
let infers = [];
let queries = [
    '#Noun #Preposition #Noun',
    '#Noun #Noun',

    // Unification rules
    '#Noun Noun #Copula (#Value|#Noun)',
    '#Noun #Preposition #Noun #Copula (#Value|#Noun)',
];

const addRule = (buf, flag) => {
    if (flag == 'sexp' || flag === undefined) {
        const terms = sexp(buf);
        let expers = terms.map((term) => {
            const newterm = term.map((exp) => {
                if (exp[0].toUpperCase() === exp[0]) {
                    return k.placeholdeR(exp);
                } else {
                    return exp;
                }
            });

            if (term[0] == 'and' || term[0] == 'or') {
                const rest = newterm.slice(1);
                return k[term[0]](...rest);
            } else {
                return newterm;
            }
        });
        console.log(expers);
        db.push(k.implies(
            ...expers
        ));
    } else if (flag === 'natural') {
        let rules = [];
        const lines = buf.split('\n');
        const matchers = queries.slice(2);
        lines.forEach((line) => {
            matchers.find((ms, matchingRule) => {
                const match = nlp(line).match(ms);
                if (match.found) {
                    if (matchingRule == 2) {
                        const [entity, attribute, _, value] = terms.data()[0];

                        let v = value.normal;
                        if (value.bestTag === 'TitleCase') {
                            v = k.placeholder(value.normal);
                        }
                        rules.push([attribute.normal, entity.normal, v]);
                    } else if (matchingRule == 3) {
                        const [attribute, prep, entity, _, value] = terms.data()[0];

                        let v = value.normal;
                        if (value.bestTag === 'TitleCase') {
                            v = k.placeholder(value.normal);
                        }
                        rules.push([attribute.normal, entity.normal, v]);
                    }
                    return true;
                }
                return false;
            });
        });

        db.push(k.implies(...rules));
    }
};

const satisfyQuery = (terms, matchingRule) => {
    let request;
    if (matchingRule == 0) {
        const [attribute, _, entity] = terms.data()[0];
        console.log([attribute.normal, entity.normal]);

        request = [attribute.normal, entity.normal, k.placeholder(uuidV4())];
    } else if (matchingRule == 1) {
        const [entity, attribute] = terms.data()[0];
        console.log([attribute.normal, entity.normal]);

        request = [attribute.normal, entity.normal.replace('\'s', ''),
                   k.placeholder(uuidV4())];
    } else if (matchingRule == 2) {
        const [entity, attribute, _, value] = terms.data()[0];
        console.log([attribute.normal, entity.normal, value.normal]);

        request = [attribute.normal, entity.normal, value.normal];
    } else if (matchingRule == 3) {
        const [attribute, prep, entity, _, value] = terms.data()[0];
        console.log([attribute.normal, entity.normal, value.normal]);

        request = [attribute.normal, entity.normal, value.normal];
    }

    return k.findValiuations(...request, known.dbsize(db));
};

// Handle requests
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
    extended: true
}));
app.post('/', (req, res) => {
    var data = req.body;
    switch (data.type) {
    case 'table':
        const [a, e, v] = [data.tableUpdate.col,
                           data.tableUpdate.row,
                           data.tableUpdate.value];
        if (typeof a !== 'string' || typeof e !== 'string' || typeof v !== 'string' ||
            a === '' || e === '' || v === '') {
            res.send({
                success: false,
                updated: 'database'
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
            data: db.filter((d) => Array.isArray(d))
        });
        break;

    case 'delete-row':
        const row = data.tableUpdate.row;
        db = db.filter((el) => {
            return el[1] !== row;
        });
        console.log(n2db);
        res.send({
            success: true,
            updated: 'database',
            data: db.filter((d) => Array.isArray(d))
        });
        break;

    case 'delete-col':
        const col = data.tableUpdate.col;
        db = db.filter((el) => {
            return el[0] !== col;
        });
        console.log(n3db);
        res.send({
            success: true,
            updated: 'database',
            data: db.filter((d) => Array.isArray(d))
        });
        break;

    case 'query':
        const foundQuery = null;

        queries.find((ms, i) => {
            let match = nlp(data.text).match(ms);
            if (match.found) {
                foundQuery = satisfyQuery(match.terms(), i);
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
        const successful = addRule(data.text, data.flag);
        res.send({
            success: successful,
            updated: 'database',
            data: null
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
app.use(express.static(path.join(__dirname, 'public/')));

app.listen(3000, function () {
    console.log('AtomicDatabase bombing you on port http://localhost:3000!');
});
