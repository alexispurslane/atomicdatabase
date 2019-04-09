from collections import namedtuple
from enum import Enum
from itertools import chain
from sexpdata import loads, dumps, Symbol
import copy

VARIABLE   = 1
EXPR       = 2
LITERAL    = 3
RULE       = 4

CONJ_OR    = 1
CONJ_AND   = 2
PREDICATE  = 3
UNIFY      = 4
PROP_GET   = 5

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

def evaluate_and_rule(db, and_clauses, binds={}, subs={}):
    if and_clauses == []:
        yield binds
    else:
        head, *tail = and_clauses
        possible = evaluate_rule(db, head, binds, subs)
        for p in possible:
            yield from evaluate_and_rule(db, tail, p, subs)

def get_variable_names(lst):
    return [name  if tpe == VARIABLE else None for (tpe, name) in lst]

def cleanse(unsafe_tail, binds, subs):
    tail = []
    print(str(subs))
    for el in unsafe_tail:
        if el[0] == VARIABLE and el[1] in subs and subs[el[1]] != None:
            print("SUBS: " + str(el[1]) + " = " + str(subs[el[1]]))
            tail.append((el[0], subs[el[1]]))
        elif type(el) == list:
            tail.append([el[0]] + cleanse(el[1:], binds, subs))
        else:
            tail.append(el)
    return tail

def evaluate_rule(db, rule, binds={}, subs={}):
    head, *tail = rule
    tail = cleanse(tail, binds, subs)
    print(head, tail)
    if head == PREDICATE:
        if tail[1][0] == LITERAL and not (tail[1][1] in db.entities) and (tail[1][1] in db.rules):
            rule = db.rules[tail[1][1]]
            var_names = get_variable_names(tail)
            params = var_names[:1] + var_names[2:]
            substitutions = dict(zip(rule["args"], params))

            print("CALL RULE:\t" + tail[1][1])
            print("PARAMS:\t" + str(params))
            print("ARGS:\t" + str(rule["args"]))

            for res in evaluate_rule(db, rule["body"], binds, subs=substitutions):
                yield { substitutions[k]: res[substitutions[k]] for k in rule["args"] if substitutions[k] }
        else:
            for (e, a, v) in db.eavs.values():
                eav_rule = [(LITERAL, db.entities[e]),
                            (LITERAL, db.attributes[a]),
                            (LITERAL, v)]
                res = unify(tail, eav_rule, copy.copy(binds))
                if res != None:
                    yield res
    elif head == UNIFY:
        res = unify(tail[0], tail[1], copy.copy(binds))
        if res != None:
            yield res
    elif head == PROP_GET:
        [ent, att, out] = tail
        if out[0][0] == VARIABLE and out[1][0].isupper():
            new_binds = copy.copy(binds)
            new_binds[out[1]] = db.get_value(ent[1], att[1])
            yield binds
    elif head == CONJ_OR:
        for tail_x in tail:
            yield from evaluate_rule(db, tail_x, copy.copy(binds), subs)
    elif head == CONJ_AND:
        yield from evaluate_and_rule(db, tail, binds, subs)

def clean_symbol(e):
    if isinstance(e, Symbol):
        return e._val
    else:
        return e

def create_rule(lst):
    rule = []
    lst = [clean_symbol(sym) for sym in lst]
    if lst[0] == "&":
        rule.append(CONJ_AND)
        for r in lst[1:]:
            rule.append(create_rule(r))
    elif lst[0] == "|":
        rule.append(CONJ_OR)
        for r in lst[1:]:
            rule.append(create_rule(r))
    elif lst[0] == "get":
        rule.append(PROP_GET)
        rule.append(lst[1])
        rule.append(lst[2])
        rule.append(lst[3])
    elif lst[0] == "unify":
        rule.append(UNIFY)
        rule.append(create_rule(lst[1])[1:])
        rule.append(create_rule(lst[2])[1:])
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
            elif type(e) == str and e[0].isupper():
                rule.append((VARIABLE, e))
            else:
                rule.append((LITERAL, e))
    return rule

class EAVDatabase:
    def __init__(self):
        self.attributes = []
        self.entities = []
        self.eavs = {}
        self.rules = {}

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
        h = eav_hash(self.entities.index(entity), self.attributes.index(attr))
        return self.eavs[h]

    def create_hashmaps_data(self):
        data = []
        for (entity, attribute, value) in sorted(self.eavs.values(), key=lambda x: x[0]):
            if entity >= len(data):
                print("creating entity " + str(entity))
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

    def add_rule(self, name, args, body):
        self.rules[name] = {
            "name": name,
            "args": args,
            "body": create_rule(loads("(& " + body + ")"))
        }
        return self

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

            .add(("mampa_cool@gmail.com", "name", "Rose Cool"))

            .add(("pamam_cool@gmail.com", "name", "Ed Cool"))

            .add(("mammam_cool@gmail.com", "name", "Julie Cool"))
            .add_rule("grandfather", ["Person", "Goal"], """
            (Person father X)
            (X father Goal)
            """)
        )



