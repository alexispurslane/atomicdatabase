/*
  This is the knowledgebase.
*/
const known = require("@shieldsbetter/known");
const k = known.kfac;

const nlp = require("compromise");

const fs = require('fs');
const path = require('path');

const express = require('express');
const app = express();


// For display purposes, remember that facts are held as AEV
let db = {};
let infers = [];
let facts = [];

app.use(express.static(path.join(__dirname, 'public/')));

app.listen(3000, function () {
    console.log('Example app listening on port http://localhost:3000!');
});
