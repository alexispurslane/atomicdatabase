import eav_database

import spacy
from spacy.matcher import Matcher

import re

PATTERNS = {
    "ReversePredicate": [
        {'DEP': 'nsubj'},
        {'LEMMA': 'be'},
        {'POS': 'DET', 'OP': '*'},
        {'DEP': 'attr'},
        {'DEP': 'prep'},
        {'DEP': 'pobj'},
    ],
    "PredicateContraction": [
        {'POS': {'IN': ['NOUN', 'PROPN']}},
        {'POS': 'PART', 'OP': '?'},
        {'DEP': 'nsubj'},
        {'LEMMA': 'be'},
        {'DEP': 'attr'}
    ],
    "Predicate": [
        {'POS': 'DET', 'OP': '*'},
        {'DEP': 'nsubj'},
        {'DEP': 'prep'},
        {'DEP': 'pobj'},
        {'LEMMA': 'be'},
        {'DEP': 'attr'},
    ],
    "SimpleQuery": [
        {'TAG': 'WP'},
        {'LEMMA': 'be'},
        {'DEP': 'poss'},
        {'POS': 'PART', 'OP': '?'},
        {'IS_ASCII': True, 'IS_SPACE': False}
    ]
}

def create_matcher(nlp):
    matcher = Matcher(nlp.vocab)

    for (k, v) in PATTERNS.items():
        print("Added " + k + " pattern.")
        matcher.add(k, None, v)

    return matcher

def create_text_entities(string):
    new_str = ""
    in_quot = False
    entities = []
    for c in string:
        if c == "\"":
            in_quot = not in_quot
            if in_quot:
                entities.append("")
            else:
                new_str += "ENTITY_" + str(len(entities) - 1)
        else:
            if in_quot:
                entities[-1] += c
            else:
                new_str += c
    return new_str, entities

def get_matches(matches, doc):
    return [(doc.vocab.strings[match_id], doc[start:end]) for match_id, start, end in matches]

def access_repeat(a, l):
     intermediate = a
     for i in l:
         intermediate = intermediate[i]
     return intermediate

def group_conjs(strings):
    paren_pos_stack = [0]
    output = []
    idx = 0
    for s in reversed([s.strip() for s in strings if len(s.strip()) > 0]):
        if s == 'then':
            s = 'and'
        if s in ['and', 'or']:
            if not (output[paren_pos_stack[-1]] in ['and', 'or']):
                output.insert(paren_pos_stack[-1], s)
                idx += 1
            elif output[paren_pos_stack[-1]] != s:
                paren_pos_stack.pop()
                output.append(')')
                output.append('(')
                output.append(s)
                paren_pos_stack.append(idx - 1)
                idx += 3
        elif s == ')':
            output.append('(')
            paren_pos_stack.append(idx + 1)
            idx += 1
        elif s == '(':
            output.append(')')
            paren_pos_stack.pop()
            idx += 1
        else:
            output.append(s)
            idx += 1

    sublisted_out = []
    in_paren = False
    current_point = []
    for out in reversed(output):
        if out == ')':
            access_repeat(sublisted_out, current_point).append([])
            current_point.append(len(access_repeat(sublisted_out, current_point)) - 1)
        elif out == '(':
            current_point.pop()
        else:
            if out == 'and':
                access_repeat(sublisted_out, current_point).insert(0, '&')
            elif out == 'or':
                access_repeat(sublisted_out, current_point).insert(0, '|')
            else:
                access_repeat(sublisted_out, current_point).append(out)
    return sublisted_out

def recursive_map(constarg, fun, lst):
    # need multiple lines of the function inside the map, but the function
    # inside the map has to have access to this one. Hence, reimplement map
    res = []
    for item in lst:
        if isinstance(item, list):
            res.append(recursive_map(constarg, fun, item))
        else:
            res.append(fun(constarg, item))
    return res

def run_nlp(constarg, string):
    (matcher, nlp) = constarg
    doc = nlp(string)
    mat = get_matches(matcher(doc), doc)
    if len(mat) > 0:
        return mat[-1]
    else:
        return string

def understand_predicate(nlp, matcher, string):
    string, entities = create_text_entities(string)
    conjugation_groups = group_conjs(re.split("( and | then | or |[()])", string))

    # No multiline lambdas means no closures, so i have to implement them manually
    return recursive_map((matcher, nlp), run_nlp, conjugation_groups), entities

RULE_IDS = {
    '&': eav_database.CONJ_AND,
    '|': eav_database.CONJ_OR,
}

def create_type(s, entities):
    if "ENTITY_" in s:
        rematch = re.search("([0-9]+)", s)
        if rematch:
            print(entities)
            number = int(rematch.group())
            return (eav_database.LITERAL, entities[number])
        else:
            return (eav_database.LITERAL, s)
    elif s[0].isupper():
        return (eav_database.VARIABLE, s.replace(".", ""))
    else:
        return (eav_database.LITERAL, s)

def convert_match_to_rule(entities, match):
    global RULE_IDS
    if isinstance(match, tuple):
        (pattern, lst) = match
        (entity, attribute, value) = (None, None, None)
        if pattern == 'SimpleQuery':
            entity = [x.text for x in lst if x.dep_ == 'poss']
            attribute = [x.text for x in lst if x.pos_ != 'PUNCT']
            return [eav_database.PREDICATE,
                    create_type(entity[0], entities),
                    create_type(attribute[-1], entities),
                    (eav_database.VARIABLE, 'Result')]
        elif pattern == 'PredicateContraction':
            entity    = [x.text for x in lst if x.pos_ in ['NOUN', 'PROPN']]
            attribute = [x.text for x in lst if x.dep_ == 'nsubj']
            value     = [x.text for x in lst if x.dep_ == 'attr']
        elif pattern == 'ReversePredicate':
            entity    = [x.text for x in lst if x.dep_ == 'pobj']
            attribute = [x.text for x in lst if x.dep_ == 'attr']
            value     = [x.text for x in lst if x.dep_ == 'nsubj']
        elif pattern == 'Predicate':
            entity    = [x.text for x in lst if x.dep_ == 'pobj']
            attribute = [x.text for x in lst if x.dep_ == 'nsubj']
            value     = [x.text for x in lst if x.dep_ == 'attr']

        if entity != None and attribute != None and value != None:
            args = [entity, attribute, value]
            return [eav_database.PREDICATE, *[create_type(x[0], entities) for x in args]]
    elif isinstance(match, str) and match in RULE_IDS:
        return RULE_IDS[match]
    else:
        return match

def convert_nlast_to_rules(ast, entities):
    res = recursive_map(entities, convert_match_to_rule, ast)
    if len(res) == 1:
        return res[0]
    else:
        return res

def pos_printer(doc):
    columns = ["TEXT", "LEMMA", "POS", "TAG", "DEP"]
    data = [[el.text, el.lemma_, el.pos_, el.tag_, el.dep_] for el in doc]

    row_format ="{:>15}" * (len(columns) + 1)
    print(row_format.format("", *columns))
    for row in data:
        print(row_format.format("", *row))


