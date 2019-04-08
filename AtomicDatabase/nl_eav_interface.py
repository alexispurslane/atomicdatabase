import eav_database

import spacy
from spacy.matcher import Matcher

import re

PATTERNS = {
    "ReversePredicate": [
        {'DEP': 'nsubj'},
        {'LEMMA': 'be'},
        {'POS': 'DET', 'OP': '*'},
        {'POS': 'NOUN'},
        {'DEP': 'prep'},
        {'DEP': 'pobj'},
    ],
    "Predicate": [
        {'POS': {'IN': ['NOUN', 'PROPN']}},
        {'POS': 'PART', 'OP': '?'},
        {'DEP': 'nsubj'},
        {'LEMMA': 'be'},
        {'DEP': 'attr'}
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
            mat = fun(constarg, item)
            if len(mat) > 0:
                res.append(mat[-1])
            else:
                res.append(item)
    return res

def run_nlp(constarg, string):
    (matcher, nlp) = constarg
    doc = nlp(string)
    return get_matches(matcher(doc), doc)

def understand_predicate(nlp, matcher, string):
    string, entities = create_text_entities(string)
    conjugation_groups = group_conjs(re.split("( and | then | or |[()])", string))

    # No multiline lambdas means no closures, so i have to implement them manually
    return recursive_map((matcher, nlp), run_nlp, conjugation_groups), entities

def pos_printer(doc):
    columns = ["TEXT", "LEMMA", "POS", "TAG", "DEP"]
    data = [[el.text, el.lemma_, el.pos_, el.tag_, el.dep_] for el in doc]

    row_format ="{:>15}" * (len(columns) + 1)
    print(row_format.format("", *columns))
    for row in data:
        print(row_format.format("", *row))


