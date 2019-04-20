import eav_database as eav_database
from utils import *

import spacy
from spacy.matcher import Matcher

import re

from io import StringIO
import sys

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

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
        {'DEP': 'poss'},
        {'POS': 'PART', 'OP': '?'},
        {'DEP': 'nsubj'},
        {'LEMMA': 'be'},
        {'DEP': {'IN': ['attr', 'acomp']}}
    ],
    "Predicate": [
        {'POS': 'DET', 'OP': '*'},
        {'DEP': 'nsubj'},
        {'DEP': 'prep'},
        {'DEP': 'pobj'},
        {'LEMMA': 'be'},
        {'DEP': {'IN': ['attr', 'acomp']}},
    ],
    "SimpleQuery": [
        {'TAG': 'WP'},
        {'LEMMA': 'be'},
        {'DEP': 'poss'},
        {'POS': 'PART', 'OP': '?'},
        {'IS_ASCII': True, 'IS_SPACE': False}
    ],
    "ReverseSimpleQuery": [
        {'TAG': 'WP'},
        {'LEMMA': 'be'},
        {'DEP': 'det'},
        {'DEP': 'nsubj'},
        {'DEP': 'prep'},
        {'DEP': 'pobj'}
    ],
    "FindEntitySimpleQuery": [
        {'TAG': 'WP'},
        {'LEMMA': 'have'},
        {'DEP': 'det'},
        {'DEP': 'dobj'},
        {'DEP': 'prep'},
        {'DEP': 'pobj'}
    ],
    "FindEntitySimpleQueryContraction": [
        {'TAG': 'WP'},
        {'LEMMA': 'be'},
        {'DEP': 'attr'},
        {'LEMMA': 'be'},
        {'DEP': {'IN': ['attr', 'ROOT']}}
    ]
}

def create_matcher(nlp):
    matcher = Matcher(nlp.vocab)

    for (k, v) in PATTERNS.items():
        print("Added " + k + " pattern.")
        matcher.add(k, None, v)

    return matcher

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
        with Capturing() as output:
            pos_printer(doc)
        raise ValueError("Can't recognize sentence '" + string + "' with format: \n" + "\n".join(output))

def understand_predicate(nlp, matcher, string):
    string, entities = create_text_entities(string)
    conjugation_groups = group_conjs(re.split("( and | then | or |[()])", string))

    # No multiline lambdas means no closures, so i have to implement them manually
    return recursive_map((matcher, nlp), run_nlp, conjugation_groups), entities

RULE_IDS = {
    '&': eav_database.CONJ_AND,
    '|': eav_database.CONJ_OR,
}

def create_type(s, entities, uuid=""):
    try:
        return (eav_database.LITERAL, int(s))
    except:
        try:
            return (eav_database.LITERAL, float(s))
        except:
            pass
    if "ENTITY_" in s:
        rematch = re.search("([0-9]+)", s)
        if rematch:
            print(entities)
            number = int(rematch.group())
            return (eav_database.LITERAL, entities[number])
        else:
            return (eav_database.LITERAL, s)
    elif s[0].isupper() and not (" " in s):
        return (eav_database.VARIABLE, s.replace(".", "")+uuid)
    else:
        return (eav_database.LITERAL, s)

def convert_match_to_rule(consts, match):
    (entities, uuid) = consts
    global RULE_IDS
    if isinstance(match, tuple):
        (pattern, lst) = match
        print(pattern, lst)
        (entity, attribute, value) = (None, None, None)
        if pattern == 'SimpleQuery':
            entity = [x.text for x in lst if x.dep_ == 'poss']
            attribute = [x.text for x in lst if x.dep_ == 'nsubj']
            value = ['Result']
        elif pattern == 'PredicateContraction':
            entity    = [x.text for x in lst if x.dep_ == 'poss']
            attribute = [x.text for x in lst if x.dep_ == 'nsubj']
            value     = [x.text for x in lst if x.dep_ == 'attr' or x.dep_ == 'acomp']
        elif pattern == 'ReversePredicate':
            entity    = [x.text for x in lst if x.dep_ == 'pobj']
            attribute = [x.text for x in lst if x.dep_ == 'attr']
            value     = [x.text for x in lst if x.dep_ == 'nsubj']
        elif pattern == 'Predicate':
            entity    = [x.text for x in lst if x.dep_ == 'pobj']
            attribute = [x.text for x in lst if x.dep_ == 'nsubj']
            value     = [x.text for x in lst if x.dep_ == 'attr' or x.dep_ == 'acomp']
        elif pattern == 'ReverseSimpleQuery':
            entity    = [x.text for x in lst if x.dep_ == 'pobj']
            attribute = [x.text for x in lst if x.dep_ == 'nsubj']
            value = ['Result']
        elif pattern == 'FindEntitySimpleQuery':
            entity    = ['Result']
            attribute = [x.text for x in lst if x.dep_ == 'dobj']
            value = [x.text for x in lst if x.dep_ == 'pobj']
        elif pattern == 'FindEntitySimpleQueryContraction':
            entity    = ['Result']
            attribute = [[x.text for x in lst if x.dep_ == 'attr'][0]]
            value = [[x.text for x in lst if x.dep_ == 'attr' or x.dep_ == 'ROOT'][2]]

        if entity != None and attribute != None and value != None:
            args = [entity, attribute, value]
            return [eav_database.PREDICATE, *[create_type(x[0], entities, uuid) for x in args]]
    elif isinstance(match, str) and match in RULE_IDS:
        return RULE_IDS[match]
    else:
        return match

def convert_nlast_to_rules(ast, entities, uuid=""):
    res = recursive_map((entities, uuid), convert_match_to_rule, ast)
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


