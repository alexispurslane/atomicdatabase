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
    features = {}
    for word in word_tokens:
        features['contains({})'.format(word.lower())] = True
    return features

def ie_preprocess_sent(stop_words, string):
    sent = nltk.word_tokenize(string)
    features = sentence_act_features(sent)
    sent = [w for w in sent if not w in stop_words]
    sent = nltk.pos_tag(sent)

    quot_sent = []
    in_quot = False
    for (x, tag) in sent:
        if tag == "``":
            in_quot = True
            quot_sent.append(("", "QQ"))
        elif tag == "''":
            in_quot = False
        elif in_quot and quot_sent[-1][1] == "QQ":
            quot_sent[-1] = (quot_sent[-1][0] + " " + x, "QQ")
        elif tag != "``" and tag != "''" and not in_quot:
            quot_sent.append((x, tag))

    return quot_sent, features

def ie_process_tok(classifier, tagged, features):
    return [(word, c) for (word, c) in tagged if c != '.'], classifier.classify(features)

def convert_to_predicate(words, stype):
