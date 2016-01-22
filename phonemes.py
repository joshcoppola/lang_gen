# coding=Latin-1

import itertools

''' 
This file deals with language building blocks (phonemes) and clusters of phonemes.
There are different valid clusters of phonemes depending on whether the cluster
occurs at the start of a syllable (onset) or at the end of a syllable (coda). 
'''


class Consonant:
    ''' A consonant is the basic building block of phoneme clusters
    for the purpose of this script. The consonant class contains 
    information about location, method, and voicing, as well as a 
    unique number, and an english letter that can correspond to the
    consonant. '''
    def __init__(self, char, num, location, method, voicing, description):
        self.char = char
        self.num = num
        self.location = location
        self.method = method
        self.voicing = voicing
        self.description = description

    def info(self):
        print 'Consonant {0} {1} {2} {3}'.format(self.num, self.location, self.method, self.voicing)

class Vowel:
    def __init__(self, char, num, position, description):
        self.char = char
        self.num = num
        # Tuple of tuples. Each sub-tuple is an xy pair of tongue position / tongue height
        # There is one xy pair for each "sound" in the vowel, so monphthongs have one sub-tuple
        # and diphthongs have two sub-tuples
        self.position = position

        self.description = description


    def info(self):
        print 'Vowel {0} {1}'.format(self.num, self.char)

    def get_string(self):
        return self.char


class PCluster:
    ''' This class contains an array of phoneme objects for 
    a single cluster. Many "clusters" are a single phoneme,
    but many contain multiple phonemes. '''
    def __init__(self, consonant_array):
        self.consonant_array = consonant_array

    def get_string(self):
        cstr = ''
        for phoneme in self.consonant_array:
            cstr += phoneme.char
        return cstr


class PClusterGenerator:
    ''' This class contains rules to generate clusters of phonemes
    A cluster can be a syllable onset or coda. Many clusters are a 
    single consonant, but there are some complex ones like "spr" 
    The clusters are defined by rules, and this class will convert 
    those rules into every possible permutation of clusters which 
    match the rules '''
    def __init__(self, property_list):
        self.property_list = property_list

    def generate(self):
        converted_to_consonants_mega_list = [] # array of arrays tracking all matching consonants
        for property in self.property_list:
            matching_consonants = find_consonants(property[0], property[1], property[2], property[3])
            converted_to_consonants_mega_list.append(matching_consonants)
        # Code found here: http://stackoverflow.com/questions/5582481/creating-permutations-from-a-multi-dimensional-array-in-ruby
        # In short, checks all permutations of a 2-dimensional array, in order
        # Here, this is checking all possible onsets / codas, given the rules definied in the input
        
        all_permutations = []

        for l in converted_to_consonants_mega_list:
            for item in itertools.product(l):
                all_permutations.append(item)
                
        # This will be a list of the posssible permutations, in consonant form
        all_permutations_worked = []

        # Check to make sure that there are no back-to-back copies of the same consonant
        # (due to the ways the rules are defined, this can occasionally happen)
        # If there are no duplicates, then create a new PCluster object and add it to the possibilities
        for i in all_permutations:
            has_duplicate_consonant = 0
            consonant_array = []
            for consonant in i:
                if len(consonant_array) > 0 and consonant.num == consonant_array[-1].num:
                    has_duplicate_consonant = 1

                consonant_array.append(consonant)
            # Only let the clusters without duplicate consonants through
            if has_duplicate_consonant == 0:
                all_permutations_worked.append(PCluster(consonant_array))

        return all_permutations_worked        
        
        
def find_consonants(location, method, voicing, exclude_list):
    ''' Given a set of parameters, return an array of consonants that match the parameters '''
    return [c for c in CONSONANTS 
                if  (location == c.location or location == 'any') 
                and (method == c.method or method == 'any') 
                and (voicing == c.voicing or voicing == 'any') 
                and c.num not in exclude_list # Sometimes there are exceptions to which consonants can match the input criteria
                ] 
        
        
# List of consonants and their properties
CONSONANTS = [ 
    Consonant('p',  201, 'bilabial',     'plosive',     0, '"p"'),
    Consonant('b',  202, 'bilabial',     'plosive',     1, '"b"'),
    Consonant('t',  203, 'alveolar',     'plosive',     0, '"t"'),
    Consonant('d',  204, 'alveolar',     'plosive',     1, '"d"'),
    Consonant('k',  205, 'velar',        'plosive',     0, '"k"'),
    Consonant('g',  206, 'velar',        'plosive',     1, 'hard "g", as in "girl"'),
    Consonant('ch', 207, 'post-alveolar','affricate',   0, '"ch", as in "chest"'),
    Consonant('j',  208, 'post-alveolar','affricate',   1, '"j", as in "join"'),
    Consonant('f',  209, 'labio-dental', 'fricative',   0, '"f"'),
    Consonant('v',  210, 'labio-dental', 'fricative',   1, '"v"'),
    Consonant('th', 211, 'dental',       'fricative',   0, 'soft "th", as in "thin"'),
    Consonant('th', 212, 'dental',       'fricative',   1, 'hard "th", as in "that"'),
    Consonant('s',  213, 'alveolar',     'fricative',   0, '"s"'),
    Consonant('z',  214, 'alveolar',     'fricative',   1, '"z"'),
    Consonant('sh', 215, 'post-alveolar','fricative',   0, '"sh", as in "shore"'),
    Consonant('zh', 216, 'post-alveolar','fricative',   1, '"zh", as the "s" in "treasure"'),
    Consonant('h',  217, 'glottal',      'fricative',   3, '"h"'),
    Consonant('m',  218, 'bilabial',     'nasal',       3, '"m"'),
    Consonant('n',  219, 'alveolar',     'nasal',       3, '"n"'),
    Consonant('ng', 220, 'velar',        'nasal',       3, '"ng", as in "thing"'),
    Consonant('r',  221, 'alveolar',     'approximant', 3, '"r"'), # R - should be also post-alveolar?
    Consonant('y',  222, 'palatal',      'approximant', 3, '"y" consonant, as in "yes"'), # J - really Y
    Consonant('w',  223, 'velar',        'approximant', 3, '"w"'),
    Consonant('l',  224, 'alveolar',     'lateral',     3, '"l"') 
    ]



# Source: https://en.wikipedia.org/wiki/Diphthong#English
# low    oʊ ~ ʌʊ   8, 5 -> 9, 7
# loud   aʊ̯~ æʊ   5, 0 -> 5, 6
# -lout             covered ^
# lied   äɪ        3, 0 -> 4, 7
# -light ʌɪ         covered ^
# lane   eɪ        0, 5 -> 3, 7
# loin   ɔɪ        9, 4 -> 5, 7
# -loon  ʉu         covered by 111
# -lean  i          covered by 102
# leer   ɪɚ 
# lair   ɛɚ
# lure   ʊɚ

VOWELS = [

    # -- Monophthongs -- #
    Vowel(char='i',  num=101, position=( (0, 7), ),  description='short "i", as in "sit"'),
    Vowel(char='e',  num=102, position=( (0, 9), ),  description='long "e", as in "see"'),
    Vowel(char='u',  num=103, position=( (5, 2), ),  description='short "u", as in "up"'),
    Vowel(char='e',  num=114, position=( (0, 5), ),  description='short "e", as in "beg"'),
    Vowel(char='a',  num=105, position=( (0, 2), ),  description='short "a", as in "bad"'),
    Vowel(char='aa', num=107, position=( (9, 1), ),  description='flat "a", as in "ah"'), #hot
    Vowel(char='oo', num=110, position=( (9, 7), ),  description='short "oo", as in "good"'),
    Vowel(char='ue', num=111, position=( (9, 9), ),  description='long "u", as in "blue"'),
    Vowel(char='au', num=112, position=( (9, 3), ),  description='"aw", as in "saw"'),

    # -- Diphthongs -- #
    Vowel(char='ae', num=106, position=( (0, 5), (3, 7) ),  description='long "a", as in "gate"'),  ## Really diphthong!
    Vowel(char='ie', num=108, position=( (3, 0), (4, 7) ),  description='long "i", as in "hide"'), #diphthong?
    Vowel(char='o',  num=109, position=( (8, 5), (9, 7) ),  description='long "o", as in "toe"'),  # diphthong
    Vowel(char='ou', num=113, position=( (5, 0), (5, 6) ),  description='"ou", as in "out"'),
    Vowel(char='oi', num=114, position=( (9, 4), (5, 7) ) , description='"oi", as in "toil"')

]

# A syllable onset is the consonant(s) which begin a syllable
POSSIBLE_ONSETS = [
    PClusterGenerator( [['bilabial', 'plosive', 0, []] ] ),
    PClusterGenerator( [['bilabial', 'plosive', 1, []] ] ),
    PClusterGenerator( [['alveolar', 'plosive', 0, []] ] ),
    PClusterGenerator( [['alveolar', 'plosive', 1, []] ] ),
    PClusterGenerator( [['velar', 'plosive', 0, []] ] ),
    PClusterGenerator( [['velar', 'plosive', 1, []] ] ),
    PClusterGenerator( [['post-alveolar', 'affricate', 0, []] ] ),
    PClusterGenerator( [['post-alveolar', 'affricate', 1, []] ] ),
    PClusterGenerator( [['labio-dental', 'fricative', 0, []] ] ),
    PClusterGenerator( [['labio-dental', 'fricative', 1, []] ] ),
    PClusterGenerator( [['dental', 'fricative', 0, []] ] ),
    PClusterGenerator( [['dental', 'fricative', 1, []] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 0, []] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 1, []] ] ),
    PClusterGenerator( [['post-alveolar', 'fricative', 0, []] ] ),
    #PClusterGenerator( [['post-alveolar', 'fricative', 1, []] ] ),
    PClusterGenerator( [['glottal', 'fricative', 3, []] ] ),
    PClusterGenerator( [['bilabial', 'nasal', 3, []] ] ),
    PClusterGenerator( [['alveolar', 'nasal', 3, []] ] ),
    #PClusterGenerator( [['velar', 'nasal', 3, []] ] ),
    PClusterGenerator( [['alveolar', 'approximant', 3, []] ] ),
    PClusterGenerator( [['palatal', 'approximant', 3, []] ] ),
    #PClusterGenerator( [['velar', 'approximant', 3, []] ] ),
    PClusterGenerator( [['alveolar', 'lateral', 3, []] ] ),
    PClusterGenerator( [['any', 'plosive', 'any', []], ['any', 'approximant', 'any', [222, 223]] ] ),
    PClusterGenerator( [['any', 'fricative', 0, []], ['any', 'approximant', 'any', [222, 223]] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 0, []], ['any', 'plosive', 0, []] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 0, []], ['any', 'nasal', 'any', [220]] ] ),
    #PClusterGenerator( [[213, 'any', []], ['fricative', 'any', 0, [211, 212, 213, 215, 216]] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 0, []], ['any', 'fricative', 0, [211, 213, 215]] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 0, []], ['any', 'plosive', 0, []], ['any', 'approximant', 'any', [222, 223]] ] )
    ]


# A syllable coda is the consonant(s) which end a syllable
POSSIBLE_CODAS =  [ 
    PClusterGenerator( [['bilabial', 'plosive', 0, []] ] ),
    PClusterGenerator( [['bilabial', 'plosive', 1, []] ] ),
    PClusterGenerator( [['alveolar', 'plosive', 0, []] ] ),
    PClusterGenerator( [['alveolar', 'plosive', 1, []] ] ),
    PClusterGenerator( [['velar', 'plosive', 0, []] ] ),
    PClusterGenerator( [['velar', 'plosive', 1, []] ] ),
    PClusterGenerator( [['post-alveolar', 'affricate', 0, []] ] ),
    PClusterGenerator( [['post-alveolar', 'affricate', 1, []] ] ),
    PClusterGenerator( [['labio-dental', 'fricative', 0, []] ] ),
    PClusterGenerator( [['labio-dental', 'fricative', 1, []] ] ),
    PClusterGenerator( [['dental', 'fricative', 0, []] ] ),
    PClusterGenerator( [['dental', 'fricative', 1, []] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 0, []] ] ),
    PClusterGenerator( [['alveolar', 'fricative', 1, []] ] ),
    PClusterGenerator( [['post-alveolar', 'fricative', 0, []] ] ),
    PClusterGenerator( [['post-alveolar', 'fricative', 1, []] ] ),
    PClusterGenerator( [['glottal', 'fricative', 3, []] ] ),
    PClusterGenerator( [['bilabial', 'nasal', 3, []] ] ),
    PClusterGenerator( [['alveolar', 'nasal', 3, []] ] ),
    PClusterGenerator( [['velar', 'nasal', 3, []] ] ),
    PClusterGenerator( [['alveolar', 'approximant', 3, []] ] ),
    PClusterGenerator( [['palatal', 'approximant', 3, []] ] ),
    #PClusterGenerator( [['velar', 'approximant', 3, []] ] ), #w
    PClusterGenerator( [['alveolar', 'lateral', 3, []] ] ),
    PClusterGenerator( [['alveolar', 'lateral', 3, []], ['any', 'plosive', 'any', []] ] ),
    PClusterGenerator( [['alveolar', 'lateral', 3,  []], ['any', 'affricate', 'any', []] ] ),
    PClusterGenerator( [['alveolar', 'approximant', 3, []], ['any', 'plosive', 'any', []] ] ),
    PClusterGenerator( [['alveolar', 'approximant', 3, []], ['any', 'affricate', 'any', []] ] ),
    PClusterGenerator( [['alveolar', 'lateral', 3, []], ['any', 'fricative', 'any', [216, 217]] ] ),
    PClusterGenerator( [['alveolar', 'approximant', 3,  []], ['any', 'fricative', 'any', [216, 217]] ] ),
    PClusterGenerator( [['alveolar', 'lateral', 3, []], ['any', 'nasal', 'any', [220]] ] ),
    PClusterGenerator( [['alveolar', 'approximant', 3, []], ['any', 'nasal', 'any', [220]] ] ),
    PClusterGenerator( [['alveolar', 'approximant', 3, []], ['any', 'lateral', 'any', []] ] ),
    PClusterGenerator( [['any', 'nasal', 'any', [220]], ['any', 'plosive', 'any', []] ] ),  ## homorganic?
    PClusterGenerator( [['any', 'nasal', 'any', [220]], ['any', 'affricate', 'any', []] ] ),## homorganic?
    PClusterGenerator( [['any', 'nasal', 'any', [220]], ['any', 'fricative', 'any', [216, 217]] ] ),
    PClusterGenerator( [['any', 'fricative', 0, [216]], ['any', 'plosive', 0, []] ] ),
    PClusterGenerator( [['any', 'plosive', 0, []], ['any', 'plosive', 0, []] ] ),
    PClusterGenerator( [['any', 'plosive', 'any', []], ['any', 'fricative', 0, [216]] ] )
    ]