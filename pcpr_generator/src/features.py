from src.constants import RELATIVE_FEATS, MAX_AFFIX_LENGTH, CONTEXT_WINDOW
import string


class Features:
    def __init__(self,sentence):
        self.sentence = sentence
        self.words = sentence['TOKENS']
        self.POS = sentence['POS']
        self.feature_rep = []
        self.punct = string.punctuation
        self.neg = ['no','not', 'n\'t','nor','neither', 'negative', 'absent', 'cannot']
        self.numlike = ['one','two','three','four','five','six','seven','eight','nine','ten']
        self.negated = False # has the sentence been negated?

    def get_static_features(self):
        for i, word in enumerate(self.words):
            pos_tag = self.POS[i]
            features = {
            'bias': 1.0,
            'pos': pos_tag,
            'negated': False,
            }
            features.update(self.orthographic_features(word))
            features.update(self.affix_features(word))
            if features['neg']:
                self.negated = True
            if i == 0:
                features['BOS'] = True
            elif i == len(self.words)-1:
                features['EOS'] = True
            self.feature_rep.append(features)
        return None

    def add_relative_features(self,offset):
        for i, word in enumerate(self.words):
            if i > (0+offset):
                self.feature_rep[i].update(
                    {'prev'+str(offset+1)+'_' + feature_name:self.feature_rep[i - (1+offset)][feature_name] for feature_name in RELATIVE_FEATS}
                )

            if i < len(self.words) - (1+offset):
                self.feature_rep[i].update(
                    {'next'+str(offset+1)+'_' + feature_name:self.feature_rep[i + (1+offset)][feature_name] for feature_name in RELATIVE_FEATS}
                )
        return None

    def include_context(self):
        for c in range(CONTEXT_WINDOW):
            self.add_relative_features(c)
        return None

    def affix_features(self,word):
        prefixes = {'prefix' + str(i): word[:i] for i in range(2, MAX_AFFIX_LENGTH)}
        suffixes = {'suffix' + str(i):word[-i:] for i in range(2,MAX_AFFIX_LENGTH)}
        prefixes.update(suffixes)
        return prefixes

    def orthographic_features(self,word):
        return {
            'length':len(word),
            'lowercase': word.lower(),
            'all_upper': word.isupper(),
            'title': word.istitle(),
            'digit': word.isdigit(),
            '>5': (2 if int(word)>5 else 1) if word.isdigit() else 0,
            'punct': word in self.punct,
            'neg': word in self.neg,
            'numlike' : word.lower() in self.numlike,
            'phi' : word.lower() == 'phi'

        }

    def get_feats(self):
        self.get_static_features()
        self.include_context()
        if self.negated:
            for i in range(self.feature_rep.__len__()):
                self.feature_rep[i]['negated'] = True
        return self.feature_rep