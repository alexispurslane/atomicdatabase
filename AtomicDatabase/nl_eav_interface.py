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
        {'POS': 'NOUN'},
        {'POS': 'PART', 'OP': '?'},
        {'DEP': 'nsubj'},
        {'LEMMA': 'be'},
        {'DEP': 'attr'},
    ],
    "SimpleQuery": [
        {'TAG': 'WP'},
        {'LEMMA': 'be'},
        {'IS_ASCII': True, 'POS': 'X'},
        {'POS': 'PART', 'OP': '?'},
        {'DEP': 'attr'},
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
    return [(nlp.vocab.strings[match_id], doc[start:end]) for match_id, start, end in matches]

def group_conjs(strings):
    collections = [['and']]
    current_conj = 'and'
    for s in strings:
        s_s = s.strip()
        print("CONJ: " + str(current_conj))
        print("STR: " + s)
        if s_s == 'and' or s_s == 'or':
            if current_conj != s_s:
                collections.append([s_s])
                current_conj = s_s
        else:
            collections[-1].append(s_s)
    return collections

def understand_predicate(matcher, string):
    string, entities = create_text_entities(string)
    conjugation_groups = group_conjs(re.split(" (and|or) ", string))

    new_groups = []
    for group in conjugation_groups:
        new_groups.append([group[0]])
        for line in group[1:]:
            doc = nlp(line)
            new_groups[-1].append(get_matches(matcher(doc), doc))
    return new_groups, entities
