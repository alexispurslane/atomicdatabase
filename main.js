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


const process = require('process');
const path = require('path');
const uuidV4 = require('uuid/v4');

const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const engine = require("./engine");

if (process.argv.length > 2 && typeof process.argv[2] === 'string') {
    engine.loadDatabase(process.argv[2]);
}
// Handle requests
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
    extended: true
}));
app.post('/', (req, res) => {
    const req_switch = {
        'reload': (data) => {
            const [d, as, es] = engine.safeDB();
            res.send({
                success: true,
                updated: null,
                data: {
                    database: d,
                    attrOrder: as,
                    entityOrder: es
                }
            });
        },
        'table': (data) => {
            const [a, e, v] = [data.tableUpdate.col.value, data.tableUpdate.row.value, data.tableUpdate.value];

            if (typeof a !== 'string' || typeof e !== 'string' || typeof v !== 'string' ||
                a === '' || e === '' || v === '') {
                res.send({
                    success: false,
                    updated: 'database',
                    data: 'Expecting valid Attributes, Entities, and Values'
                });
                return;
            }

            // Keep track
            engine.updateDatabase(a, e, v, data.tableUpdate.col.index, data.tableUpdate.row.index);
            const [d, as, es] = engine.safeDB();

            res.send({
                success: true,
                updated: 'database',
                data: {
                    database: d,
                    attrOrder: as,
                    entityOrder: es
                }
            });
        },

        'delete-row': (data) => {
            const row = data.tableUpdate.row;
            if (typeof row !== "string") {
                res.send({
                    success: false,
                    updated: 'database',
                    data: 'Expecting a valid row.'
                });
                return;
            }

            engine.deleteRow(row);
            const [d, as, es] = engine.safeDB();
            res.send({
                success: true,
                updated: 'database',
                data: {
                    database: d,
                    attrOrder: as,
                    entityOrder: es
                }
            });
        },

        'delete-col': (data) => {
            const col = data.tableUpdate.col;
            if (typeof col !== "string") {
                res.send({
                    success: false,
                    updated: 'database',
                    data: 'Expecting a valid column.'
                });
                return;
            }

            engine.deleteCol(col);
            const [d, as, es] = engine.safeDB();
            res.send({
                success: true,
                updated: 'database',
                data: {
                    database: d,
                    attrOrder: as,
                    entityOrder: es
                }
            });
        },

        'query': (data) => {
            if (data.text.length === 0 || typeof data.text !== 'string') {
                res.send({
                    success: false,
                    updated: 'query-engine',
                    data: "Expected valid query."
                });
            } else {
                let foundQuery = engine.satisfyQuery(data.text);

                res.send({
                    success: !!foundQuery,
                    updated: 'query-engine',
                    data: foundQuery
                });
            }
        },

        'rule': (data) => {
            const results = engine.addRule(data.title, data.text, data.flag);
            const successful = engine.isUnderstood(results);

            if (successful) {
                engine.rememberRule(results, data);
            }

            res.send({
                success: successful,
                updated: 'rules',
                data: results
            });
        },

        'save': (data) => {
            if (process.argv.length > 2 && typeof process.argv[2] === 'string') {
                engine.saveDatabase();
                res.send({
                    success: true,
                    updated: 'file',
                    data: process.argv[2]
                });
            }

            res.send({
                success: false,
                updated: 'file',
                data: 'Server has no file to save to.'
            });
        },

        'delete-rule': (data) => {
            res.send({
                success: engine.deleteRule(data.title),
                updated:'rules'
            });
        },

        'rules': (data) => {
            res.send({
                success: true,
                updated: null,
                data: engine.getRules()
            });
        },

        'default': (data) => {
            res.send({
                success: false,
                updated: null,
                data: 'Unknown command.'
            });
        }
    };

    if (req_switch.hasOwnProperty(req.body.type)) {
        console.log("Calling " + req.body.type);
        req_switch[req.body.type](req.body);
    } else {
        console.log("Unrecognized hook " + req.body.type);
        req_switch['default'](req.body);
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
