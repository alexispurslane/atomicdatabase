import re
import os
import hashlib
from collections import namedtuple
from utils import *
from enum import Enum
from itertools import chain
from sexpdata import loads, dumps, Symbol, Bracket
import copy
import inspect
import pickle
import json
from functools import wraps

import resource, sys
resource.setrlimit(resource.RLIMIT_STACK, (2**29, -1))
sys.setrecursionlimit(10**6)

#  ____  _____ _       _____             _
# / ___|| ____| |     | ____|_ __   __ _(_)_ __   ___
# \___ \|  _| | |     |  _| | '_ \ / _` | | '_ \ / _ \
#  ___) | |___| |___  | |___| | | | (_| | | | | |  __/
# |____/|_____|_____| |_____|_| |_|\__, |_|_| |_|\___|
#                                 |___/

VARIABLE   = 1
EXPR       = 2
LITERAL    = 3
RULE       = 4
LIST       = 5

CONJ_OR    = 1 + 5
CONJ_AND   = 2 + 5
PREDICATE  = 3 + 5
UNIFY      = 4 + 5
CONJ_COMP  = 5 + 5
CONJ_COND  = 6 + 5
BUILTIN    = 7 + 5


def ast_value_wrap(val, decend=True):
    if is_variable(val):
        return (VARIABLE, val)
    elif isinstance(val, list):
        if decend:
            val = [ast_value_wrap(v) for v in val]
        return (LIST, val)
    else:
        return (LITERAL, val)

def unify(a, b, binds={}, global_binds={}):
    for i in range(0, min(len(a), len(b))):
        (a_type, a_val) = a[i]
        (b_type, b_val) = b[i]

        if (a_type == LIST and is_destructuring_pattern(a_val) and (b_type == LIST or b_type == VARIABLE)) or\
           (b_type == LIST and is_destructuring_pattern(b_val) and (a_type == LIST or a_type == VARIABLE)):
            if a_type == VARIABLE:
                var_a_val = get_binds(a_val, binds, global_binds)
                if var_a_val == None:
                    raise ValueError("Undefined variable " + str(a_val))
                else:
                    a_val = var_a_val

            if b_type == VARIABLE:
                var_b_val = get_binds(b_val, binds, global_binds)
                if var_b_val == None:
                    raise ValueError("Undefined variable " + str(b_val))
                else:
                    b_val = var_b_val

            if is_destructuring_pattern(b_val):
                a_val, b_val = b_val, a_val
                a_type, b_type = b_type, a_type

            a_val = [(get_binds(v, binds, global_binds) or v) if t == VARIABLE else v for t, v in a_val]
            b_val = [get_binds(v, binds, global_binds) if t == VARIABLE else v for t, v in b_val]
            new_binds = destructure(a_val, b_val)
            if new_binds != None:
                binds_so_far = copy.copy(binds)
                for binding in new_binds:
                    # side1 doesn't need to be wrapped *internally* because the
                    # value substituted into the call by `get_binds` isn't ever
                    # unwrapped! However, it does need to be wrapped on the outside.
                    side1 = ast_value_wrap(binding[0], False)
                    side2 = ast_value_wrap(binding[1])
                    res = unify([side1], [side2], copy.copy(binds_so_far), global_binds)
                    if res != None:
                        binds_so_far = res
                    else:
                        return None
                binds = binds_so_far
            else:
                return None
        elif a_type == LIST and b_type == LIST:
            if len(a_val) != len(b_val):
                return None
            else:
                res = unify(a_val, b_val, copy.copy(binds), global_binds)
                if res == None:
                    return None
                else:
                    binds = res
        elif (b_type == LIST and a_type == VARIABLE) or (a_type == LIST and b_type == VARIABLE):
            if b_type == VARIABLE:
                a_val, b_val = b_val, a_val
                a_type, b_type = b_type, a_type

            a_kval = get_binds(a_val, binds, global_binds)
            if a_kval != None and isinstance(a_kval, list):
                new_binds = unify([(b_type, b_val)], [(LIST, a_kval)], copy.copy(binds), global_binds)
                if new_binds != None:
                    binds.update(new_binds)
                else:
                    return None
            elif a_kval == None:
                binds[a_val] = b_val
            else:
                return None
        elif (a_type == VARIABLE and b_type == LITERAL) or (b_type == VARIABLE and a_type == LITERAL):
            if b_type == VARIABLE:
                a_val, b_val = b_val, a_val
                a_type, b_type = b_type, a_type

            a_kval = get_binds(a_val, binds, global_binds)
            if a_kval != None and a_kval == b_val:
                continue
            elif not a_kval:
                binds[a_val] = b_val
            else:
                return None
        elif a_type == LITERAL and b_type == LITERAL:
            if a_val == b_val:
                continue
            else:
                return None
        elif a_type == VARIABLE and b_type == VARIABLE:
            a_kval = get_binds(a_val, binds, global_binds)
            b_kval = get_binds(b_val, binds, global_binds)

            if a_kval != None and b_kval != None and a_kval == b_kval:
                continue
            elif not a_kval:
                binds[a_val] = b_kval
            elif not b_kval:
                binds[b_val] = a_kval
            else:
                return None
    return binds

types = [
    { "name": "OR Conjugation", "arg_count": (1, -1) },
    { "name": "AND Conjugation", "arg_count": (1, -1) },
    { "name": "PREDICATE or RULE", "arg_count": (2, -1) },
    { "name": "UNIFY Command", "arg_count": (2, 2) },
    { "name": "COMPARASON Conjugation", "arg_count": (3, 3) },
    { "name": "CONDITION Conjugation", "arg_count": (1, -1) },
]

def evaluate_exprs(lst, binds):
    res = []
    for e in lst:
        if e[0] == EXPR:
            res.append((LITERAL, eval_expr(e[1], binds)))
        elif e[0] == LIST:
            res.append((LIST, evaluate_exprs(e[1], binds)))
        else:
            res.append(e)
    return res

SPECIAL_RULES = {
    "print": lambda tail: print("\nInternal AD Log: " + str(tail[-1])),
}

def evaluate_and_rule(db, and_clauses, binds, subs):
    if and_clauses == []:
        yield binds
    else:
        head, *tail = and_clauses
        possible = evaluate_rule(db, head, binds, subs)
        for p in possible:
            yield from evaluate_and_rule(db, tail, p, subs)

def evaluate_rule(db, rule, binds={}, subs={}):
    global types

    head, *tail = rule

    max_args = types[head-6]["arg_count"][1]
    min_args = types[head-6]["arg_count"][0]
    if len(tail) < min_args:
        raise ValueError("Not enough elements in " + types[head-1]["name"] +\
                         "! Expected at least "+str(min_args)+", found " + str(len(tail)) + ".")
    elif len(tail) > max_args and max_args != -1:
        raise ValueError("Too many elements in " + types[head-1]["name"] +\
                         "! Expected less than "+str(max_args)+", found " + str(len(tail)) + ".")

    tail = evaluate_exprs(tail, binds)

    if head == PREDICATE:
        was_rule = False
        if tail[1][0] == LITERAL and not (tail[1][1] in db.entities) and (tail[1][1] in db.rules or tail[1][1] in SPECIAL_RULES):
            name = tail[1][1]
            was_rule = True

            tail = [(LITERAL, binds[name])
                    if tpe == VARIABLE and name in binds
                    else (tpe, name)
                    for tpe, name in tail]

            sr = SPECIAL_RULES.get(name)
            if sr:
                res = sr(tail)
                if res:
                    yield from res
                else:
                    yield binds
            else:
                rule = db.rules[name]
                if len(tail) - 1 != len(rule["args"]):
                    raise ValueError("Wrong number of arguments in " + rule["name"].upper() +\
                                     " Rule! Expected "+str(len(rule["args"]))+", found " + str(len(tail)) + ".")

                var_names = [name if tpe == VARIABLE else None for (tpe, name) in tail]
                params = var_names[:1] + var_names[2:]
                substitutions = dict(zip(rule["args"], params))

                lit_vals = [val if tpe == LITERAL or tpe == LIST else None for (tpe, val) in tail]
                inputs = lit_vals[:1] + lit_vals[2:]
                input_binds = { k: v for k, v in zip(rule["args"], inputs) if v != None }

                print("STACK DEPTH: " + str(len(inspect.stack())))

                for res in evaluate_rule(db, rule["body"], input_binds, subs=substitutions):
                    output_binds = { substitutions[key]: value
                                     for key, value in res.items()
                                     if key in substitutions and substitutions[key] }
                    for key, value in binds.items():
                        if not key in output_binds:
                            output_binds[key] = value

                    yield output_binds

        if not was_rule:
            if len(tail) < 3:
                raise ValueError("Not enough elements in PREDICATE" + \
                                 "! Expected at least 3, found " + str(len(tail)) + ".")
            if tail[0][0] == LITERAL and tail[1][0] == LITERAL and tail[2][0] == LITERAL:
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
                                ast_value_wrap(v, False)]
                    res = unify(tail, eav_rule, copy.copy(binds), db.global_binds)
                    if res != None:
                        yield res
    elif head == CONJ_COMP:
        op, *args = tail
        vals = []
        for e in args:
            if e[0] == VARIABLE:
                val = get_binds(e[1], binds, db.global_binds)
                if val != None:
                    vals.append(val)
                else:
                    raise ValueError("Undefined variable " + e[1] + "!")
            else:
                vals.append(e[1])
        failed = False
        last = None
        for v in vals:
            choice = False
            if last != None:
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
        res = unify([tail[0]], [tail[1]], new_binds, db.global_binds)
        if res != None:
            yield res
    elif head == CONJ_OR:
        for tail_x in tail:
            yield from evaluate_rule(db, tail_x, copy.copy(binds), subs)
    elif head == CONJ_COND:
        for branch in tail:
            ret = evaluate_rule(db, branch, copy.copy(binds), subs)
            try:
                fst = next(ret)
                yield from chain([fst], ret)
                break
            except StopIteration:
                continue
    elif head == CONJ_AND:
        yield from evaluate_and_rule(db, tail, binds, subs)

def clean_symbol(e):
    if isinstance(e, Symbol):
        return e._val
    else:
        return e

def create_datatype(e, entities):
    if isinstance(e, Bracket):
        return (LIST, [create_datatype(clean_symbol(sym), entities)
                       for sym in e._val])
    elif isinstance(e, str) and "ENTITY_" in e:
        rematch = re.search("([0-9]+)", e)
        if rematch:
            number = int(rematch.group())
            return (LITERAL, entities[number])
        else:
            return (LITERAL, e)
    elif is_variable(e):
        return (VARIABLE, e)
    else:
        return (LITERAL, e)

def create_rule(lst, entities):
    rule = []
    lst = [clean_symbol(sym) for sym in lst]
    if lst[0] == "&":
        rule.append(CONJ_AND)
        for r in lst[1:]:
            rule.append(create_rule(r, entities))
    elif lst[0] == "|":
        rule.append(CONJ_OR)
        for r in lst[1:]:
            rule.append(create_rule(r, entities))
    elif lst[0] == "?":
        rule.append(CONJ_COND)
        for r in lst[1:]:
            rule.append(create_rule(r, entities))
    elif lst[0] in ["<", ">", "<=", ">="]:
        rule.append(CONJ_COMP)
        rule.append(lst[0])
        rule.extend(create_rule(lst[1:], entities)[1:])
    elif lst[0] == "=":
        rule.append(UNIFY)
        rule.append(create_rule([lst[1]], entities)[1])
        rule.append(create_rule(lst[2:], entities)[1])
    else:
        rule.append(PREDICATE)
        in_expr = False
        expr = []
        for e in lst:
            if e == "{":
                in_expr = True
                expr = []
            elif e == "}":
                in_expr = False
                rule.append((EXPR, expr))
            elif in_expr:
                expr.append(e)
            else:
                rule.append(create_datatype(e, entities))
    return rule

def body(st):
    new_body, entities = create_text_entities("(& " + st + ")")
    return create_rule(loads(new_body), entities), st

#  _____    ___     __  ____        _        _
# | ____|  / \ \   / / |  _ \  __ _| |_ __ _| |__   __ _ ___  ___
# |  _|   / _ \ \ / /  | | | |/ _` | __/ _` | '_ \ / _` / __|/ _ \
# | |___ / ___ \ V /   | |_| | (_| | || (_| | |_) | (_| \__ \  __/
# |_____/_/   \_\_/    |____/ \__,_|\__\__,_|_.__/ \__,_|___/\___|

class EAVDatabase:
    def __init__(self, **args):
        self.attributes = []
        self.attribute_metadata = {}
        self.entities = []
        self.eavs = {}
        self.global_binds = {}
        self.rules = {}
        self.type_name = ["entity", "string", "int", "float"]
        if args != {}:
            args["eavs"] = { float(k): v for k, v in args["eavs"].items() }
            self.__dict__.update(args)

    def validate(self, data, attr, value):
        actual_type = 1
        if isinstance(value, str) and value in self.entities:
            actual_type = 0
        elif isinstance(value, str):
            actual_type = 1
        elif isinstance(value, int):
            actual_type = 2
        elif isinstance(value, float):
            actual_type = 3

        if data["type"] != actual_type:
            raise TypeError("Wrong type for " + attr + ". Expected " + self.type_name[data["type"]] +\
                            ", got " + self.type_name[actual_type] + "!")

        is_ok = data["type"] == 0 and (value in self.entities) or\
            data["type"] == 1 and isinstance(value, str) and (not data["allowed_strings"] or\
                                                                value in data["allowed_strings"] or\
                                                                len(data["allowed_strings"]) == 0) or\
            (data["type"] == 2 or data["type"] == 3) and between_limits(value, data["num_limits"])

        custom_message = ""
        if data["type"] == 0:
            custom_message = " from: " + limit_format(self.entities) + "..."
        elif data["type"] == 1:
            custom_message = " from: " + limit_format(data["allowed_strings"])
        elif data["type"] == 2 or data["type"] == 3 and data["num_limits"]:
            custom_message = " between " + limit_format(data["num_limits"][0]) + " and " +\
                limit_format(data["num_limits"][1]) + " (inclusive)"

        if not is_ok:
            raise ValueError("Incorrect type for attribute " + attr + ". Expected " +\
                            self.type_name[data["type"]] + custom_message + ", got: " + str(value) + ".")

    def change_attribute_metadata(self, attr, new):
        self.attribute_metadata[attr] = new

    def add_rule(self, name, rule_args=[], new_rule={
            "lang": 0,
            "text": "",
            "body": ""
        }):
        new_rule.update({
            "name": name,
            "args": rule_args,
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

        if attr in self.attribute_metadata:
            data = self.attribute_metadata[attr]

            if not data.get("is_list"):
                self.validate(data, attr, value)
            else:
                for v in value:
                    self.validate(data, attr, v[1])

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
    outfile = open(os.path.expanduser(os.path.expandvars(name)),'w')
    json.dump(db.__dict__, outfile)
    outfile.close()

def load_from_file(name):
    print("Load from: " + name)
    infile = open(os.path.expanduser(os.path.expandvars(name)),'r')
    db = EAVDatabase(**json.load(infile))
    infile.close()
    return db

