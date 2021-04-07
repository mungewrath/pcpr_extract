### CRF CONSTANTS ###

RELATIVE_FEATS = ['lowercase','pos', 'all_upper','title','digit','neg', 'numlike']  # the features of words in context to include for the current word
MAX_AFFIX_LENGTH = 3  # length of prefix and suffixes to be included (starting from 2)
CONTEXT_WINDOW = 2  # number of words before and after to include in context for a given word (greatly increases train time)

"""
Feature Descriptions:
---------------------
prev_X_...- feature from the token X positions before the current token
next_X_...- feature from the token X positions after the current token
lowercase - lowercase representation of a token
pos -       part-of-speech
all_upper - it the entire token uppercase?
title -     Is only the first letter capitalized?
digit -     Is the token a digit?
numlike-    Is it a written out number?
neg-        Is negation word? **need to expand this/may be redundant when using POS tags**
phi-        Is PHI?
"""


special_char_replacement = {
    '§': 5,
    '$': 5,
    'β': 8,
    'ϐ': 8
}

text_numbers = {"one":1,
                'two':2,
                'three':3,
                'four':4,
                'five':5,
                'six':6,
                'seven':7,
                'eight':8,
                'nine':9,
                'ten':10}

# Keys are the fields on our annotation features sheets. Values are keyword arrays, and the last index of these arrays will be used for word distance to catch for bad OCR
# ||| in the last element if you want multiple test strings for word distance
extra_info ={'Seminal Vesicle +?':['seminal','vesicle','seminal vesicle involement'],
             'Extraprostatic extension/involvement of periprostatic fat?':['extraprostatic','extension','periprostatic','extraprostatic extension'],
             'Perineural/peripheral nerve or angiolymphatic/vascular invasion?':['perineural','peripheral nerve','angiolymphatic invasion|||vascular invasion'],
             'Rare cancer subtype?':['ductal','intraductal'],
             'HGPIN?':['high grade','hgpin', 'pin','high-grade prostatic intraepithelial neoplasia'],
             'ASAP?':['asap','acinar proliferation','atypical small acinar proliferation'],
             'atypical glands?':['glands','atypical glands'], # 'atypical' is NOT a suitable keyword
            'suspicious for cancer?':['suspicious', 'carcinoma','']

             }
