import re
import os
import hashlib
from collections import namedtuple
from utils import *
from enum import Enum
from itertools import chain
from sexpdata import loads, dumps, Symbol
import copy
import inspect
import pickle

VARIABLE   = 1
EXPR       = 2
LITERAL    = 3
RULE       = 4

CONJ_OR    = 1
CONJ_AND   = 2
PREDICATE  = 3
UNIFY      = 4
CONJ_COMP  = 5
CONJ_COND  = 6

def eav_hash(a, b):
    return 0.5*(a + b)*(a + b + 1)+b

def eval_expr(val, binds):
    return eval(" ".join([str(binds[el]) if el in binds else str(el) for el in val]), {}, {})

def unify(a, b, binds={}):
    for i in range(0, min(len(a), len(b))):
        (a_type, a_val) = a[i]
        (b_type, b_val) = b[i]
        if a_type == EXPR:
            a_type = LITERAL
            a_val = eval_expr(a_val, binds)
        if b_type == EXPR:
            b_type = LITERAL
            b_val = eval_expr(b_val, binds)

        if a_type == LITERAL and b_type == LITERAL:
            if a_val == b_val:
                continue
            else:
                return None
        elif a_type == VARIABLE and b_type == LITERAL:
            a_kval = binds.get(a_val)
            if a_kval and a_kval == b_val:
                continue
            elif not a_kval:
                binds[a_val] = b_val
            else:
                return None
        elif b_type == VARIABLE and a_type == LITERAL:
            b_kval = binds.get(b_val)
            if b_kval and b_kval == a_val:
                continue
            elif not b_kval:
                binds[b_val] = a_val
            else:
                return None
        elif a_type == VARIABLE and b_type == VARIABLE:
            a_kval = binds.get(a_val)
            b_kval = binds.get(b_val)

            if a_kval == b_kval:
                continue
            else:
                return None
    return binds

def peek(iterable):
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return chain([first], iterable)

def evaluate_cond_rule(db, branches, binds={}, subs={}):
    if branches == []:
        return None
    else:
        head, *tail = branches
        print("COND BRANCH: " + str(head))
        print("BINDS: " + str(binds))
        ret = evaluate_rule(db, head, binds, subs)
        try:
            fst = next(ret)
            yield from chain([fst], ret)
        except StopIteration:
            print("No stuff")
            yield from evaluate_cond_rule(db, tail, binds, subs)

def evaluate_and_rule(db, and_clauses, binds={}, subs={}):
    if and_clauses == []:
        yield binds
    else:
        head, *tail = and_clauses
        possible = evaluate_rule(db, head, binds, subs)
        for p in possible:
            yield from evaluate_and_rule(db, tail, p, subs)

def evaluate_rule(db, rule, binds={}, subs={}):
    head, *tail = rule
    print(head, tail)
    if head == PREDICATE:
        if tail[1][0] == LITERAL and not (tail[1][1] in db.entities) and (tail[1][1] in db.rules):
            rule = db.rules[tail[1][1]]

            tail = [(LITERAL, binds[name])
                    if tpe == VARIABLE and name in binds
                    else (tpe, name)
                    for tpe, name in tail]
            var_names = [name if tpe == VARIABLE else None for (tpe, name) in tail]
            params = var_names[:1] + var_names[2:]
            substitutions = dict(zip(rule["args"], params))

            lit_vals = [val if tpe == LITERAL else None for (tpe, val) in tail]
            inputs = lit_vals[:1] + lit_vals[2:]
            input_binds = { k: v for k, v in zip(rule["args"], inputs) if v }
            for key, value in binds.items():
                if not key in input_binds:
                    input_binds[key] = value

            print("CALL RULE:\t" + tail[1][1])
            print("PARAMS:\t" + str(params))
            print("ARGS:\t" + str(rule["args"]))
            print("BINDINGS: " + str(input_binds))

            for res in evaluate_rule(db, rule["body"], input_binds, subs=substitutions):
                output_binds = { substitutions[key]: value for key, value in res.items() if key in substitutions and substitutions[key] }
                for key, value in binds.items():
                    if not key in output_binds:
                        output_binds[key] = value

                yield output_binds
        elif tail[0][0] == LITERAL and tail[1][0] == LITERAL and tail[2][0] == VARIABLE:
            res = db.get_value(tail[0][1], tail[1][1])
            if res:
                new_binds = copy.copy(binds)
                new_binds[tail[2][1]] = res
                yield new_binds
        elif tail[0][0] == LITERAL and tail[1][0] == LITERAL and tail[2][0] == LITERAL:
            res = db.get_value(tail[0][1], tail[1][1])
            if res and res == tail[2][1]:
                yield binds
            elif not res:
                db.add((tail[0][1], tail[1][1], tail[2][1]))
                yield binds
        else:
            for (e, a, v) in db.eavs.values():
                eav_rule = [(LITERAL, db.entities[e]),
                            (LITERAL, db.attributes[a]),
                            (LITERAL, v)]
                res = unify(tail, eav_rule, copy.copy(binds))
                if res != None:
                    yield res
    elif head == CONJ_COMP:
        op, *args = tail
        vals = [binds[e[1]] if e[0] == VARIABLE and e[1] in binds else e[1] for e in args]
        failed = False
        last = None
        for v in vals:
            choice = False
            if last:
                if op == "<":
                    choice = v > last
                elif op == ">":
                    choice = v < last
                elif op == ">=":
                    choice = v <= last
                elif op == "<=":
                    choice = v >= last
            if choice or last is None:
                last = v
            else:
                failed = True
                break
        if not failed:
            yield binds
    elif head == UNIFY:
        new_binds = copy.copy(binds)
        res = unify(tail[0], tail[1], new_binds)
        if res != None:
            yield res
    elif head == CONJ_OR:
        for tail_x in tail:
            yield from evaluate_rule(db, tail_x, copy.copy(binds), subs)
    elif head == CONJ_COND:
        print("COND BODY: " + str(tail))
        yield from evaluate_cond_rule(db, tail, binds, subs)
    elif head == CONJ_AND:
        yield from evaluate_and_rule(db, tail, binds, subs)

def clean_symbol(e):
    if isinstance(e, Symbol):
        return e._val
    else:
        return e

def create_rule(lst, entities, uuid=None):
    rule = []
    lst = [clean_symbol(sym) for sym in lst]
    if lst[0] == "&":
        rule.append(CONJ_AND)
        for r in lst[1:]:
            rule.append(create_rule(r, entities, uuid))
    elif lst[0] == "|":
        rule.append(CONJ_OR)
        for r in lst[1:]:
            rule.append(create_rule(r, entities, uuid))
    elif lst[0] == "?":
        rule.append(CONJ_COND)
        for r in lst[1:]:
            rule.append(create_rule(r, entities, uuid))
    elif lst[0] in ["<", ">", "<=", ">="]:
        rule.append(CONJ_COMP)
        rule.append(lst[0])
        rule.extend(create_rule(lst[1:], entities, uuid)[1:])
    elif lst[0] == "unify":
        rule.append(UNIFY)
        rule.append(create_rule(lst[1], entities, uuid)[1:])
        rule.append(create_rule(lst[2], entities, uuid)[1:])
    else:
        rule.append(PREDICATE)
        in_expr = False
        expr = []
        for e in lst:
            if e == "expr":
                in_expr = not in_expr
                if in_expr:
                    expr = []
                else:
                    rule.append((EXPR, expr))
            elif in_expr:
                expr.append(e)
            elif isinstance(e, str) and "ENTITY_" in e:
                rematch = re.search("([0-9]+)", e)
                if rematch:
                    number = int(rematch.group())
                    rule.append((LITERAL, entities[number]))
                else:
                    rule.append((LITERAL, e))
            elif isinstance(e, str) and e[0].isupper() and not " " in e:
                if uuid:
                    e += uuid
                rule.append((VARIABLE, e))
            else:
                rule.append((LITERAL, e))
    return rule

def body(st, uuid=None):
    new_body, entities = create_text_entities("(& " + st + ")")
    return create_rule(loads(new_body), entities, uuid), inspect.cleandoc(st)

class EAVDatabase:
    def __init__(self):
        self.attributes = []
        self.attribute_metadata = {}
        self.entities = []
        self.eavs = {}
        self.rules = {}

    def add_rule(self, name, rule_args=[], uuid="", new_rule={
            "lang": 0,
            "text": "",
            "body": ""
        }):
        new_rule.update({
            "name": name,
            "args": [arg+uuid for arg in rule_args],
        })
        self.rules[name] = new_rule

    def get_or_add_entity_id(self, entity):
        forein_entity = -1
        try:
            forein_entity = self.entities.index(entity)
        except:
            self.entities.append(entity)
            forein_entity = len(self.entities) - 1
        return forein_entity

    def get_or_add_attribute_id(self, attr):
        forein_attr = -1
        try:
            forein_attr = self.attributes.index(attr)
        except:
            self.attributes.append(attr)
            forein_attr = len(self.attributes) - 1
        return forein_attr

    def add(self, eav):
        (entity, attr, value) = eav
        forein_entity = self.get_or_add_entity_id(entity)
        forein_attr = self.get_or_add_attribute_id(attr)

        self.eavs[eav_hash(forein_entity, forein_attr)] = (forein_entity, forein_attr, value)

        return self

    def remove_value(self, entity, attr):
        try:
            h = eav_hash(self.entities.index(entity), self.attributes.index(attr))
            if h in self.eavs: del self.eavs[h]
        except:
            print("Entity or Attribute " + str((entity, attr)) + " not found in database.")

    def get_attributes_values(self, entity):
        e = self.entities.index(entity)
        return (eav for (h, eav) in self.eavs.items() if eav[0] == e)

    def get_entities_values(self, attribute):
        ai = self.attributes.index(attribute)
        return (eav for (h, eav) in self.eavs.items() if eav[1] == ai)

    def get_value(self, entity, attr):
        if not (entity in self.entities) or (not attr in self.attributes):
            return None
        h = eav_hash(self.entities.index(entity), self.attributes.index(attr))
        if h in self.eavs:
            return self.eavs[h][2]
        else:
            return None

    def create_hashmaps_data(self):
        data = []
        for (entity, attribute, value) in sorted(self.eavs.values(), key=lambda x: x[0]):
            if entity >= len(data):
                data.insert(entity, { "entity": self.entities[entity] })
                data[entity][self.attributes[attribute]] = value

        return data

    def create_table_data(self):
        data = self.create_hashmaps_data()

        for h in data:
            for attr in self.attributes:
                if not attr in h.keys():
                    h[attr] = False

        return data

    def load_examples(self):
        (
            self.add(("cool@gmail.com", "name", "Joe Cool"))
            .add(("cool@gmail.com", "father", "pa_cool@gmail.com"))
            .add(("cool@gmail.com", "mother", "mam_cool@gmail.com"))

            .add(("stop@gmail.com", "name", "No-Stop Cool"))
            .add(("stop@gmail.com", "father", "pa_cool@gmail.com"))
            .add(("stop@gmail.com", "mother", "mammam_cool@gmail.com"))

            .add(("pa_cool@gmail.com", "name", "Kent Cool"))
            .add(("pa_cool@gmail.com", "father", "papa_cool@gmail.com"))
            .add(("pa_cool@gmail.com", "mother", "mampa_cool@gmail.com"))

            .add(("mam_cool@gmail.com", "name", "Ruby Cool"))
            .add(("mam_cool@gmail.com", "father", "pamam_cool@gmail.com"))
            .add(("mam_cool@gmail.com", "mother", "mammam_cool@gmail.com"))

            .add(("papa_cool@gmail.com", "name", "John Cool"))
            .add(("papa_cool@gmail.com", "age", 56))

            .add(("mampa_cool@gmail.com", "name", "Rose Cool"))
            .add(("mampa_cool@gmail.com", "age", 53))

            .add(("pamam_cool@gmail.com", "name", "Ed Cool"))
            .add(("pamam_cool@gmail.com", "age", 58))

            .add(("mammam_cool@gmail.com", "name", "Julie Cool"))
            .add(("mammam_cool@gmail.com", "age", 59))
        )

def save_to_file(db, name):
    print("Saved to: " + name)
    outfile = open(os.path.expanduser(os.path.expandvars(name)),'wb')
    pickle.dump(db, outfile)
    outfile.close()

def load_from_file(name):
    print("Load from: " + name)
    infile = open(os.path.expanduser(os.path.expandvars(name)),'rb')
    db = pickle.load(infile)
    infile.close()
    return db

