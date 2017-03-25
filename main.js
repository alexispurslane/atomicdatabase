/*
  This is the knowledgebase.
*/
const known = require("@shieldsbetter/known");
const k = known.kfac;

const nlp = require("compromise");

const fs = require('fs');

const express = require('express');
const app = express();


// For display purposes, remember that facts are held as AEV
let db = {};
let infers = [];
let facts = [];

app.get('/:name', (req, res, next) => {
    var options = {
        root: __dirname + '/public/',
        dotfiles: 'deny',
        headers: {
            'x-timestamp': Date.now(),
            'x-sent': true
        }
    };

    var fileName = req.params.name;
    res.sendFile(fileName, options, (err) => {
        if (err) {
            next(err);
        } else {
            console.log('served ' + fileName);
        }
    });
});

app.listen(3000, function () {
    console.log('Example app listening on port 3000!');
});
