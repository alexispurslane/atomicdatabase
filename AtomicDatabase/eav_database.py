from collections import namedtuple
from enum import Enum
from itertools import chain
import copy

VARIABLE   = 1
EXPR       = 2
LITERAL    = 3

CONJ_OR    = 1
CONJ_AND   = 2
PREDICATE  = 3

def eav_hash(a, b):
    return 0.5*(a + b)*(a + b + 1)+b

def unify(a, b, binds={}):
    for i in range(0, min(len(a), len(b))):
        (a_type, a_val) = a[i]
        (b_type, b_val) = b[i]

        if a_type == EXPR:
            a_val = eval(a_val)
            a_type = LITERAL
        if b_type == EXPR:
            b_val = eval(b_val)
            b_type = LITERAL

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

def evaluate_rule(db, rule, binds={}):
    head, *tail = rule
    if head == PREDICATE:
        for (e, a, v) in db.eavs.values():
            eav_rule = [(LITERAL, db.entities[e]),
                        (LITERAL, db.attributes[a]),
                        (LITERAL, v)]
            res = unify(tail, eav_rule, copy.copy(binds))
            if res:
                yield res
    elif head == CONJ_OR:
        [tail_a, tail_b] = tail
        res_a = evaluate_rule(db, tail_a, copy.copy(binds))
        res_b = evaluate_rule(db, tail_b, copy.copy(binds))
        yield from chain(res_a, res_b)
    elif head == CONJ_AND:
        [tail_a, tail_b] = tail
        res_a = evaluate_rule(db, tail_a, copy.copy(binds))
        for possible_binds in res_a:
            res_b = evaluate_rule(db, tail_b, copy.copy(possible_binds or {}))
            yield from res_b

class EAVDatabase:
    def __init__(self):
        self.attributes = []
        self.entities = []
        self.eavs = {}

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

    def load_examples(self):
        self.add(("cool@gmail.com", "name", "Joe Cool"))
        self.add(("cool@gmail.com", "father", "pa_cool@gmail.com"))
        self.add(("cool@gmail.com", "mother", "mam_cool@gmail.com"))

        self.add(("stop@gmail.com", "name", "No-Stop Cool"))
        self.add(("stop@gmail.com", "father", "pa_cool@gmail.com"))
        self.add(("stop@gmail.com", "mother", "mammam_cool@gmail.com"))

        self.add(("pa_cool@gmail.com", "name", "Kent Cool"))
        self.add(("pa_cool@gmail.com", "father", "papa_cool@gmail.com"))
        self.add(("pa_cool@gmail.com", "mother", "mampa_cool@gmail.com"))

        self.add(("mam_cool@gmail.com", "name", "Ruby Cool"))
        self.add(("mam_cool@gmail.com", "father", "pamam_cool@gmail.com"))
        self.add(("mam_cool@gmail.com", "mother", "mammam_cool@gmail.com"))

        self.add(("papa_cool@gmail.com", "name", "John Cool"))

        self.add(("mampa_cool@gmail.com", "name", "Rose Cool"))

        self.add(("pamam_cool@gmail.com", "name", "Ed Cool"))

        self.add(("mammam_cool@gmail.com", "name", "Julie Cool"))



