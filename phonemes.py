# coding=Latin-1

import itertools
from collections import Counter

''' 
This file deals with language building blocks (phonemes) and clusters of phonemes.
There are different valid clusters of phonemes depending on whether the cluster
occurs at the start of a syllable (onset) or at the end of a syllable (coda). 
'''

# For lack of a better location, this maps the
VOICING_DESCRIPTIONS = {0: ' unvoiced', 1:' voiced', 3:'', 'any':''}

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
    def __init__(self, char, num, position, length, description):
        self.char = char
        self.num = num
        # Tuple of tuples. Each sub-tuple is an xy pair of tongue position / tongue height
        # There is one xy pair for each "sound" in the vowel, so monphthongs have one sub-tuple
        # and diphthongs have two sub-tuples
        self.position = position

        # Short, long, or diphthong
        self.length = length

        self.description = description

    def is_diphthong(self):
        return len(self.position) > 1

    def info(self):
        print 'Vowel {0} {1}'.format(self.num, self.char)

    def get_string(self):
        return self.char


class PCluster:
    ''' This class contains an array of phoneme objects for 
    a single cluster. Many "clusters" are a single phoneme,
    but many contain multiple phonemes. '''
    def __init__(self, cluster_loc, consonant_array, rule_set):
        self.cluster_loc = cluster_loc
        
        # Contains the raw consonants
        self.consonant_array = consonant_array
        # Contains the unique numbers for the consonants
        self.consonant_number_array = [c.num for c in self.consonant_array]

        self.rule_set = rule_set

    def is_empty(self):
        ''' Use to see if this cluster is simply a empty phoneme placeholder '''
        return self.consonant_array[0].num >= 300

    def is_complex(self):
        return len(self.consonant_array) > 1

    def has_all_phonemes(self, phoneme_nums):
        return all(phoneme_num in self.consonant_number_array for phoneme_num in phoneme_nums)

    def has_any_phoneme(self, phoneme_nums):
        return any(phoneme_num in self.consonant_number_array for phoneme_num in phoneme_nums)

    def get_string(self):
        cstr = ''
        for phoneme in self.consonant_array:
            cstr += phoneme.char
        return cstr


class PClusterGenerator:
    ''' This class contains rules to generate clusters of phonemes. A cluster
    can be a syllable onset or coda. Many clusters are a single consonant, but
    there are some complex ones like "spr". The clusters are defined by rules,
    and this class will convert those rules into every possible permutation of
    clusters which match the rules '''
    def __init__(self, cluster_loc, *phoneme_properties):
        self.cluster_loc = cluster_loc
        self.phoneme_properties = phoneme_properties

        rule_descriptions = [rule.describe_rule() for rule in self.phoneme_properties]
        self.rule_set = ' followed by '.join(rule_descriptions)

    def generate(self):
        ''' Generates specific Phoneme Cluster objects (PCluster) from a set of
            rules defined in self.property_list '''
        # array of arrays tracking all matching consonants
        converted_to_consonants_mega_list = [find_consonants(property.location, property.method, property.voicing, property.exceptions) for property in self.phoneme_properties]

        # Take the 2D array defined in the input, and create all permutations that the rules generalize to.
        # For example, this will transform [[A, B], [C, D], [E]] into [[A, C, E], [A, D, E], [B, C, E], [B, D, E]]
        # In this case, A, B, C, ... are particular phonemes which match the criteria in self.property_list
        all_permutations = itertools.product(*converted_to_consonants_mega_list)

        # Filter out any cluster which contains repeated phonemes (Certain generalized rules can cause this to occur)
        # and create the actual phoneme cluster object from this.
        all_permutations_worked = [PCluster(self.cluster_loc, permutation, self.rule_set) for permutation in all_permutations
                                     if all((phoneme_occurence == 1 for phoneme_occurence in Counter(permutation).values())) ]

        return all_permutations_worked        
        

class Rule:
    def __init__(self, location, method, voicing, exceptions):
        self.location = location
        self.method = method
        self.voicing = voicing
        self.exceptions = exceptions

    def describe_rule(self):
        ''' Convert a set of phoneme properties in the plain English '''

        # Find the descrition from a dict of voicing: plain_english
        voicing_description = VOICING_DESCRIPTIONS[self.voicing]

        # Some (inefficient) list comprehension magic to get a list of the consonants which are called out as exceptions in this rule
        exception_list = ['/{0}/'.format(c.char) for consonant_num in self.exceptions for c in CONSONANTS if c.num == consonant_num]
        # Turn the exception list into a string which can be tacked on at the end of the rule description
        # TODO - Use join_list() once integrated back into the project
        exceptions = '' if not len(self.exceptions) else ' (with the exception of {0})'.format(', '.join(exception_list))

        ## ------------------------------------------------------------------------------------------------------------------
        ## First - find all the consonants that match the input. If there's just one, we can call out the consonant directly
        ## ------------------------------------------------------------------------------------------------------------------
        consonants = find_consonants(self.location, self.method, self.voicing, self.exceptions)
        if len(consonants) == 1:
            description = '/{0}/'.format(consonants[0].char)

        ## ------------------------------------------------------------
        ## Else, build up a string describing properties of this rule.
        ## ------------------------------------------------------------

        ## If both the location and method are described, build a string like 'a voiced bilabial plosive'
        elif self.location != 'any' and self.method !='any':
            description = '{0} {1} {2}{3}'.format(voicing_description, self.location, self.method, exceptions)
            description = description.strip()
            description = 'an ' + description if description[0] in 'aeiou' else 'a ' + description

        ## If the location can be anything, and method is described, build a string like 'any voiced plosive'
        elif self.location == 'any' and self.method != 'any':
            description = '{0}{1} {2}{3}'.format(self.location, voicing_description, self.method, exceptions)

        ## If the location is described, and method can be anything, build a string like 'any voiced bilabial'
        elif self.location != 'any' and self.method == 'any':
            description = '{0}{1} {2}{3}'.format(self.method, voicing_description, self.location, exceptions)

        ## Should never have a rule like this - to print an error. TODO - log this
        elif self.location == 'any' and self.method == 'any':
            print "ERROR: Phoneme rule specifies any location and any method"

        return description


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
    # Consonant('zh', 216, 'post-alveolar','fricative',   1, '"zh", as the "s" in "treasure"'),
    Consonant('h',  217, 'glottal',      'fricative',   3, '"h"'),
    Consonant('m',  218, 'bilabial',     'nasal',       3, '"m"'),
    Consonant('n',  219, 'alveolar',     'nasal',       3, '"n"'),
    Consonant('ng', 220, 'velar',        'nasal',       3, '"ng", as in "thing"'),
    Consonant('r',  221, 'alveolar',     'approximant', 3, '"r"'), # R - should be also post-alveolar?
    Consonant('y',  222, 'palatal',      'approximant', 3, '"y" consonant, as in "yes"'), # J - really Y
    Consonant('w',  223, 'velar',        'approximant', 3, '"w"'),
    Consonant('l',  224, 'alveolar',     'lateral',     3, '"l"'), 

    # Empty word-initial onset
    Consonant('',   300, 'onset',        'word-initial',       3, ''),
    # Empty word-final coda
    Consonant('',   301, 'coda',         'word-final',       3, ''),
    # Empty mid-word onset
    Consonant('',   302, 'onset',        'mid-word-initial',       3, ''),
    # Empty mid-word coda
    Consonant('',   303, 'coda',         'mid-word-final',       3, '') 
    ]


# Source: https://en.wikipedia.org/wiki/Diphthong#English
# low    oʊ ~ ʌʊ   8, 5 -> 9, 7
# loud   aʊ̯~ æʊ    5, 0 -> 5, 6
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
    Vowel(char='i',  num=101, position=( (0, 7), ),  length='short', description='short "i", as in "sit"'),     # /ɪ/
    Vowel(char='e',  num=102, position=( (0, 9), ),  length='long' , description='long "e", as in "see"'),      # /i(ː)/
    Vowel(char='u',  num=103, position=( (5, 2), ),  length='short', description='short "u", as in "up"'),      # /ʌ/
    Vowel(char='e',  num=114, position=( (0, 5), ),  length='short', description='short "e", as in "beg"'),     # /ɛ/
    Vowel(char='a',  num=105, position=( (0, 2), ),  length='short', description='short "a", as in "bad"'),     # /æ/
    Vowel(char='aa', num=107, position=( (9, 1), ),  length='long' , description='flat "a", as in "ah"'),       # /ɑ/
    Vowel(char='oo', num=110, position=( (9, 7), ),  length='short', description='short "i", as in "put"'),     # /ʊ/
    Vowel(char='ue', num=111, position=( (9, 9), ),  length='long' , description='long "u", as in "blue"'),     # /uː/
    Vowel(char='au', num=112, position=( (9, 3), ),  length='long' , description='"aw", as in "saw"'),          # /ɔ/

    # -- Diphthongs -- #
    Vowel(char='ae', num=106, position=( (0, 5), (3, 7) ),  length='diphthong', description='long "a", as in "gate"'),  # eɪ
    Vowel(char='ie', num=108, position=( (3, 0), (4, 7) ),  length='diphthong', description='long "i", as in "hide"'),  # äɪ
    Vowel(char='o',  num=109, position=( (8, 5), (9, 7) ),  length='diphthong', description='long "o", as in "toe"'),   # oʊ
    Vowel(char='ou', num=113, position=( (5, 0), (5, 6) ),  length='diphthong', description='"ou", as in "out"'),       # aʊ
    Vowel(char='oi', num=114, position=( (9, 4), (5, 7) ),  length='diphthong', description='"oi", as in "toil"')       # ɔɪ

]

ID_TO_PHONEME = {phoneme.num: phoneme for phoneme in itertools.chain(CONSONANTS, VOWELS)}


# A syllable onset is the consonant(s) which begin a syllable
POSSIBLE_ONSETS = [
    PClusterGenerator( 'onset', Rule('bilabial', 'plosive', 0, []) ),
    PClusterGenerator( 'onset', Rule('bilabial', 'plosive', 1, []) ),
    PClusterGenerator( 'onset', Rule('alveolar', 'plosive', 0, []) ),
    PClusterGenerator( 'onset', Rule('alveolar', 'plosive', 1, []) ),
    PClusterGenerator( 'onset', Rule('velar', 'plosive', 0, []) ),
    PClusterGenerator( 'onset', Rule('velar', 'plosive', 1, []) ),
    PClusterGenerator( 'onset', Rule('post-alveolar', 'affricate', 0, []) ),
    PClusterGenerator( 'onset', Rule('post-alveolar', 'affricate', 1, []) ),
    PClusterGenerator( 'onset', Rule('labio-dental', 'fricative', 0, []) ),
    PClusterGenerator( 'onset', Rule('labio-dental', 'fricative', 1, []) ),
    PClusterGenerator( 'onset', Rule('dental', 'fricative', 0, []) ),
    PClusterGenerator( 'onset', Rule('dental', 'fricative', 1, []) ),
    PClusterGenerator( 'onset', Rule('alveolar', 'fricative', 0, []) ),
    PClusterGenerator( 'onset', Rule('alveolar', 'fricative', 1, []) ),
    PClusterGenerator( 'onset', Rule('post-alveolar', 'fricative', 0, []) ),
    #PClusterGenerator( [['post-alveolar', 'fricative', 1, []] ] ),
    PClusterGenerator( 'onset', Rule('glottal', 'fricative', 3, []) ),
    PClusterGenerator( 'onset', Rule('bilabial', 'nasal', 3, []) ),
    PClusterGenerator( 'onset', Rule('alveolar', 'nasal', 3, []) ),
    #PClusterGenerator( [['velar', 'nasal', 3, []] ] ),
    PClusterGenerator( 'onset', Rule('alveolar', 'approximant', 3, []) ),
    PClusterGenerator( 'onset', Rule('palatal', 'approximant', 3, []) ),
    PClusterGenerator( 'onset', Rule('velar', 'approximant', 3, []) ), # w  -- originally had been commented out
    PClusterGenerator( 'onset', Rule('alveolar', 'lateral', 3, []) ),

    # ---------------------------------------------------------- #
    PClusterGenerator( 'onset', Rule('any', 'plosive', 'any', []),
                                Rule('any', 'approximant', 'any', [222, 223]) ),

    PClusterGenerator( 'onset', Rule('any', 'plosive', 'any', []),
                                Rule('any', 'lateral', 'any', [222, 223]) ),
    # ---------------------------------------------------------- #

    # ---------------------------------------------------------- #
    PClusterGenerator( 'onset', Rule('any', 'fricative', 0, [213, 216]),
                                Rule('any', 'approximant', 'any', [222, 223]) ),

    PClusterGenerator( 'onset', Rule('any', 'fricative', 0, [213, 216]),
                                Rule('any', 'lateral', 'any', [222, 223]) ),
    # ---------------------------------------------------------- #

    PClusterGenerator( 'onset', Rule('alveolar', 'fricative', 0, []),
                                Rule('any', 'plosive', 0, []) ),

    PClusterGenerator( 'onset', Rule('alveolar', 'fricative', 0, []), 
                                Rule('any', 'nasal', 'any', [220]) ),

    #PClusterGenerator( [[213, 'any', []], ['fricative', 'any', 0, [211, 212, 213, 215, 216]] ] ),
    PClusterGenerator( 'onset', Rule('alveolar', 'fricative', 0, []), 
                                Rule('any', 'fricative', 0, [211, 213, 215]) ),

    # ---------------------------------------------------------- #
    PClusterGenerator( 'onset', Rule('alveolar', 'fricative', 0, []), 
                                Rule('any', 'plosive', 0, []), 
                                Rule('any', 'approximant', 'any', [222, 223]) )
    # spl
    # PClusterGenerator( Rule('alveolar', 'fricative', 0, []),
    #                    Rule('any', 'plosive', 0, [203, 205]),
    #                    Rule('any', 'lateral', 'any', [222, 223]) )
    # ---------------------------------------------------------- #
    ]


# A syllable coda is the consonant(s) which end a syllable
POSSIBLE_CODAS =  [
    PClusterGenerator( 'coda', Rule('bilabial', 'plosive', 0, []) ),
    PClusterGenerator( 'coda', Rule('bilabial', 'plosive', 1, []) ),
    PClusterGenerator( 'coda', Rule('alveolar', 'plosive', 0, []) ),
    PClusterGenerator( 'coda', Rule('alveolar', 'plosive', 1, []) ),
    PClusterGenerator( 'coda', Rule('velar', 'plosive', 0, []) ),
    PClusterGenerator( 'coda', Rule('velar', 'plosive', 1, []) ),
    PClusterGenerator( 'coda', Rule('post-alveolar', 'affricate', 0, []) ),
    PClusterGenerator( 'coda', Rule('post-alveolar', 'affricate', 1, []) ),
    PClusterGenerator( 'coda', Rule('labio-dental', 'fricative', 0, []) ),
    PClusterGenerator( 'coda', Rule('labio-dental', 'fricative', 1, []) ),
    PClusterGenerator( 'coda', Rule('dental', 'fricative', 0, []) ),
    PClusterGenerator( 'coda', Rule('dental', 'fricative', 1, []) ),
    PClusterGenerator( 'coda', Rule('alveolar', 'fricative', 0, []) ),
    PClusterGenerator( 'coda', Rule('alveolar', 'fricative', 1, []) ),
    PClusterGenerator( 'coda', Rule('post-alveolar', 'fricative', 0, []) ),
    PClusterGenerator( 'coda', Rule('post-alveolar', 'fricative', 1, []) ),
    # PClusterGenerator( Rule('glottal', 'fricative', 3, []) ), # /h/
    PClusterGenerator( 'coda', Rule('bilabial', 'nasal', 3, []) ),
    PClusterGenerator( 'coda', Rule('alveolar', 'nasal', 3, []) ),
    PClusterGenerator( 'coda', Rule('velar', 'nasal', 3, []) ),
    PClusterGenerator( 'coda', Rule('alveolar', 'approximant', 3, []) ),
    # PClusterGenerator( Rule('palatal', 'approximant', 3, []) ), #/j/  (like in pure, cute, ...)
    #PClusterGenerator( [['velar', 'approximant', 3, []] ] ), #w
    PClusterGenerator( 'coda', Rule('alveolar', 'lateral', 3, []) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'lateral', 3, []), 
                               Rule('any', 'plosive', 'any', []) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'lateral', 3,  []), 
                               Rule('any', 'affricate', 'any', []) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'approximant', 3, []), 
                               Rule('any', 'plosive', 'any', []) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'approximant', 3, []), 
                               Rule('any', 'affricate', 'any', []) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'lateral', 3, []),
                               Rule('any', 'fricative', 'any', [216, 217]) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'approximant', 3,  []), 
                               Rule('any', 'fricative', 'any', [216, 217]) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'lateral', 3, []), 
                               Rule('any', 'nasal', 'any', [220]) ),

    # -------  In rhotic varieties, /r/ + nasal or lateral: /rm/, /rn/, /rl/
    PClusterGenerator( 'coda', Rule('alveolar', 'approximant', 3, []), 
                               Rule('any', 'nasal', 'any', [220]) ),

    PClusterGenerator( 'coda', Rule('alveolar', 'approximant', 3, []), 
                               Rule('any', 'lateral', 'any', []) ),
    # ----------------------------------------------------------------------

    # ------- Nasal + homorganic stop or affricate: /mp/, /nt/, /nd/, /ntʃ/, /ndʒ/, /ŋk/
    # PClusterGenerator( Rule('any', 'nasal', 'any', [220]),
    #                    Rule('any', 'plosive', 'any', []) ),  ## homorganic?
    #
    # PClusterGenerator( Rule('any', 'nasal', 'any', [220]),
    #                    Rule('any', 'affricate', 'any', []) ),## homorganic?

    # /nt/, /nd/
    PClusterGenerator( 'coda', Rule('alveolar', 'nasal', 'any', []),
                               Rule('alveolar', 'plosive', 'any', []) ),

    PClusterGenerator( 'coda', Rule('bilabial', 'nasal', 'any', []),
                               Rule('bilabial', 'plosive', 0, []) ),
    # ----------------------------------------------------------------------

    # ------- Nasal + fricative: /mf/, /mθ/, /nθ/, /ns/, /nz/, /ŋθ/ in some varieties
    # TODO - worth including?
    # PClusterGenerator( Rule('any', 'nasal', 'any', [220]),
    #                    Rule('any', 'fricative', 'any', [216, 217]) ),
    #
    # ----------------------------------------------------------------------

    # ------- Voiceless fricative plus voiceless stop: /ft/, /sp/, /st/, /sk/
    PClusterGenerator( 'coda', Rule('alveolar', 'fricative', 0, []),
                               Rule('any', 'plosive', 0, []) ),

    PClusterGenerator( 'coda', Rule('labio-dental', 'fricative', 0, []),
                               Rule('alveolar', 'plosive', 0, []) ),
    # ----------------------------------------------------------------------

    # ------- "Two voiceless stops: /pt/ , /kt/ ------- #
    # It appears as though only the above are valid, so this is being de-generalized for now
    # into the next two rules
    #PClusterGenerator( Rule('any', 'plosive', 0, []),
    #                   Rule('any', 'plosive', 0, []) ),
    # /pt/
    PClusterGenerator( 'coda', Rule('bilabial', 'plosive', 0, []),
                               Rule('alveolar', 'plosive', 0, []) ),
    # /kt/
    PClusterGenerator( 'coda', Rule('velar', 'plosive', 0, []),
                               Rule('alveolar', 'plosive', 0, []) ),
    # ------- ------- ------- ------- ------- ------- ---

    # ------- "Stop plus voiceless fricative:  /pθ/, /ps/, /tθ/, /ts/, /dθ/, /ks/ ------- #
    # It looks like the below rule is too generalized; so this is being de-generalized for now
    # PClusterGenerator( Rule('any', 'plosive', 'any', []),
    #                    Rule('any', 'fricative', 0, [216]) )

    # /pθ/, /ps/, /tθ/, /ts/
    PClusterGenerator( 'coda', Rule('any', 'plosive', 0, [205]),
                               Rule('any', 'fricative', 0, [209, 215]) ),
    # /ks/
    PClusterGenerator( 'coda', Rule('velar', 'plosive', 0, []),
                               Rule('alveolar', 'fricative', 0, []) ),
    # /dθ/
    PClusterGenerator( 'coda', Rule('alveolar', 'plosive', 1, []),
                               Rule('dental', 'fricative', 0, []) )
    ]


EMPTY_CONSONANTS = [
    # Word-initial empty syllable onset
    PCluster(cluster_loc='onset', consonant_array=[ID_TO_PHONEME[300]], rule_set='empty word-initial onset'),
    # Word-final empty syllable coda
    PCluster(cluster_loc='coda', consonant_array=[ID_TO_PHONEME[301]], rule_set='empty word-final coda')
    ]



ALL_ONSETS = [onset for onset_rules in POSSIBLE_ONSETS for onset in onset_rules.generate()]
ALL_CODAS = [coda for coda_rules in POSSIBLE_CODAS for coda in coda_rules.generate()]

CONSONANT_METHODS = ('plosive', 'affricate', 'fricative', 'nasal', 'approximant', 'lateral')
CONSONANT_LOCATIONS = ('bilabial', 'alveolar', 'velar', 'post-alveolar', 'labio-dental', 
                        'dental', 'glottal', 'palatal')


