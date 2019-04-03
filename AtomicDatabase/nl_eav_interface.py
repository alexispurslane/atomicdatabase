import eav_database

import nltk
import pickle
from nltk.corpus import stopwords
from nltk.stem import LancasterStemmer
from nltk import word_tokenize, pos_tag, ne_chunk
from nltk.chunk import conlltags2tree, tree2conlltags
nltk.download('nps_chat')

CLASSIFIER_FILE_LOC = "naivebayes.pickle"

def make_utility_objects():
    stop_words = set(stopwords.words('english'))
    stemmer = LancasterStemmer()
    return stop_words, stemmer

def get_classifier():
    try:
        print('Loading classifier from file...')

        classifier_f = open(CLASSIFIER_FILE_LOC, "rb")
        classifier = pickle.load(classifier_f)
        classifier_f.close()

        return classifier
    except:
        print('No file found. Training new classifier...')
        posts = nltk.corpus.nps_chat.xml_posts()[:10000]
        featuresets = [(sentence_act_features(nltk.word_tokenize(post.text)), post.get('class')) for post in posts]
        size = int(len(featuresets) * 0.1)
        train_set, test_set = featuresets[size:], featuresets[:size]
        classifier = nltk.NaiveBayesClassifier.train(train_set)

        print('Trained Sentence Classifier: ' + str(nltk.classify.accuracy(classifier, test_set)))
        classifier.show_most_informative_features(5)

        save_classifier = open(CLASSIFIER_FILE_LOC, "wb+")
        pickle.dump(classifier, save_classifier)
        save_classifier.close()

        return classifier

def sentence_act_features(word_tokens):
    print(word_tokens)
    features = {}
    for word in word_tokens:
        features['contains({})'.format(word.lower())] = True
    return features

def sanitize_quots(w):
    (word, tag) = w
    if tag == "QQ":
        return "something"
    else:
        return word

def ie_preprocess_sent(stop_words, string):
    reverse = False
    punc = None

    sent = nltk.word_tokenize(string)
    sent = [w for w in sent if not w in stop_words]

    sent = nltk.pos_tag(sent)

    if sent[-1][1] == ".":
        punc = sent[-1]

    quot_sent = []
    in_quot = False
    for (x, tag) in sent:
        if tag == "``":
            in_quot = True
            quot_sent.append(("", "QQ"))
        elif tag == "''":
            in_quot = False
        elif in_quot and quot_sent[-1][1] == "QQ":
            leading = ""
            if len(quot_sent[-1][0]) > 0:
                leading = quot_sent[-1][0] + " "
            quot_sent[-1] = (leading + x, "QQ")
        elif tag != "``" and tag != "''" and not in_quot:
            quot_sent.append((x, tag))

    features = sentence_act_features([sanitize_quots(w) for w in quot_sent])
    print(features)

    if reverse:
        if punc:
            quot_sent = quot_sent[:-1]
        quot_sent.reverse()
        if punc:
            quot_sent.append(punc)

    return quot_sent, features

def ie_process_tok(classifier, tagged, features):
    return [(word, c) for (word, c) in tagged if c != '.'], classifier.classify(features)

def ie_process_eav(words):
    entity = None
    attribute = None
    value = None
    for (word, tag) in words:
        if not entity and (tag == "QQ" or tag == "NNP" or tag == "NN" or tag == "JJ"):
            entity = word
        elif not attribute and ("NN" in tag):
            attribute = word
        elif not value and attribute and entity:
            value = word

    try:
        value = float(value)
    except ValueError:
        pass
    return (entity.replace(" ", ""), attribute, value)

def ie_process_predicate(words):
    entity = None
    attribute = None
    value = None
    for (word, tag) in words:
        if not entity and (tag == "QQ" or tag == "NNP" or tag == "NN" or tag == "JJ" or tag == "VBD"):
            word = word.replace(" ", "")
            if "NN" in tag and word[0].isupper():
                entity = (eav_database.VARIABLE, word)
            else:
                entity = (eav_database.LITERAL, word)
        elif not attribute and ("NN" in tag):
            if word[0].isupper():
                attribute = (eav_database.VARIABLE, word)
            else:
                attribute = (eav_database.LITERAL, word)
        elif not value and attribute and entity:
            if "NN" in tag and word[0].isupper():
                value = (eav_database.VARIABLE, word)
            else:
                value = (eav_database.LITERAL, word)

    if value[0] == eav_database.LITERAL:
        try:
            value = (value[0], float(value[1]))
        except ValueError:
            pass
    return [entity, attribute, value]

RULE = 1
NEW_DATA = 2
UNKNOWN = 3
def ie_convert_dispatch(words, stype):
    if stype == "Clarify" or "Answer" in stype or stype == "Statement":
        return NEW_DATA, ie_process_eav(words)
    elif "Question" in stype:
        return RULE, ie_process_predicate(words)
    else:
        return UNKNOWN, None
