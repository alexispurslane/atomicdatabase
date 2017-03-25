/*
  This is the knowledgebase.
*/
const known = require("@shieldsbetter/known");
const k = known.kfac;

const nlp = require("compromise");

const fs = require('fs');
const csv = require('csv');

const express = require('express');
const app = express();


// For display purposes, remember that facts are held as AEV
let db = {};
let infers = [];
let facts = [];
