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
    def __init__(self, id_, char, location, method, voicing, description):
        self.id_ = id_
        self.char = char
        self.location = location
        self.method = method
        self.voicing = voicing
        self.description = description

    def info(self):
        print 'Consonant {0} {1} {2} {3}'.format(self.id_, self.location, self.method, self.voicing)

class Vowel:
    def __init__(self, id_, char, position, manner, lips, description):
        self.id_ = id_
        self.char = char
        # Tuple of tuples. Each sub-tuple is an xy pair of tongue position / tongue height
        # There is one xy pair for each "sound" in the vowel, so monphthongs have one sub-tuple
        # and diphthongs have two sub-tuples
        self.position = position

        # Lax or tense
        self.manner = manner
        # Are lips rounded or unrounded?
        self.lips = lips

        self.description = description

    def is_diphthong(self):
        return len(self.position) > 1

    def info(self):
        print 'Vowel {0} {1}'.format(self.id_, self.char)

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
        self.consonant_id_array = [c.id_ for c in self.consonant_array]

        self.rule_set = rule_set

    def is_empty(self):
        ''' Use to see if this cluster is simply a empty phoneme placeholder '''
        return self.consonant_array[0].id_ >= 300

    def is_complex(self):
        return len(self.consonant_array) > 1

    def has_all_phonemes(self, phoneme_ids):
        return all(phoneme_id in self.consonant_id_array for phoneme_id in phoneme_ids)

    def has_any_phoneme(self, phoneme_ids):
        return any(phoneme_id in self.consonant_id_array for phoneme_id in phoneme_ids)

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
        exception_list = ['/{0}/'.format(c.char) for consonant_id in self.exceptions for c in CONSONANTS if c.id_ == consonant_id]
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
                and c.id_ not in exclude_list # Sometimes there are exceptions to which consonants can match the input criteria
                ]

        
# List of consonants and their properties
CONSONANTS = [ 
    Consonant(201, 'p',  'bilabial',     'plosive',     0, '"p"'),
    Consonant(202, 'b',  'bilabial',     'plosive',     1, '"b"'),
    Consonant(203, 't',  'alveolar',     'plosive',     0, '"t"'),
    Consonant(204, 'd',  'alveolar',     'plosive',     1, '"d"'),
    Consonant(205, 'k',  'velar',        'plosive',     0, '"k"'),
    Consonant(206, 'g',  'velar',        'plosive',     1, 'hard "g", as in "girl"'),
    Consonant(207, 'ch', 'post-alveolar','affricate',   0, '"ch", as in "chest"'),
    Consonant(208, 'j',  'post-alveolar','affricate',   1, '"j", as in "join"'),
    Consonant(209, 'f',  'labio-dental', 'fricative',   0, '"f"'),
    Consonant(210, 'v',  'labio-dental', 'fricative',   1, '"v"'),
    Consonant(211, 'th', 'dental',       'fricative',   0, 'soft "th", as in "thin"'),
    Consonant(212, 'th', 'dental',       'fricative',   1, 'hard "th", as in "that"'),
    Consonant(213, 's',  'alveolar',     'fricative',   0, '"s"'),
    Consonant(214, 'z',  'alveolar',     'fricative',   1, '"z"'),
    Consonant(215, 'sh', 'post-alveolar','fricative',   0, '"sh", as in "shore"'),
    # Consonant(216, 'zh', 'post-alveolar','fricative',   1, '"zh", as the "s" in "treasure"'),
    Consonant(217, 'h',  'glottal',      'fricative',   3, '"h"'),
    Consonant(218, 'm',  'bilabial',     'nasal',       3, '"m"'),
    Consonant(219, 'n',  'alveolar',     'nasal',       3, '"n"'),
    Consonant(220, 'ng', 'velar',        'nasal',       3, '"ng", as in "thing"'),
    Consonant(221, 'r',  'alveolar',     'approximant', 3, '"r"'), # R - should be also post-alveolar?
    Consonant(222, 'y',  'palatal',      'approximant', 3, '"y" consonant, as in "yes"'), # J - really Y
    Consonant(223, 'w',  'velar',        'approximant', 3, '"w"'),
    Consonant(224, 'l',  'alveolar',     'lateral',     3, '"l"'),

    # Empty word-initial onset
    Consonant(300, '',   'onset',        'word-initial', 3, ''),
    # Empty word-final coda
    Consonant(301, '',   'coda',         'word-final',   3, ''),

    Consonant(230, 'kn',  'palatal',    'nasal',        0, '"ny" sound'),           # ɲ̊
    Consonant(231, 'gn',  'palatal',    'nasal',        1, '"ny" sound'),           # ɲ
    Consonant(232, 'cy',  'palatal',    'stop',         0, '"cy" sound'),           # c
    Consonant(233, 'gy',  'palatal',    'stop',         1, '"gy" sound'),           # ɟ
    Consonant(234, 'ts',  'alveolar',   'affricate',    0, '"\'s" as in \'sup'),    # ts (Sibilant affricate)
    Consonant(235, 'dz',  'alveolar',   'affricate',    1, '"dz" as in "adze" '),   # dz (Sibilant affricate)
    Consonant(236, 'xh',  'velar',      'fricative',    0, '"ch" in Scottish "loch"'),      # x
    Consonant(237, 'gh',  'velar',      'fricative',    1, '"gh" in Scottish "laghail"'),   # ɣ
    Consonant(238, 'r~',  'alveolar',   'trill',        1, 'rolled "r"'),          # r
    Consonant(239, 'b~',  'bilabial',   'trill',        1, 'rolled "b"')          # B
    # Consonant(240, '\'',  'glottal',    'stop',         0, 'glottal stop, as in the middle sound of "uh-oh"')  # ʔ
    ]


# NON_ENGLISH_CONSONANTS = [
#     Consonant(230, 'kn',  'palatal',    'nasal',        0, '"ny" sound'),           # ɲ̊
#     Consonant(231, 'gn',  'palatal',    'nasal',        1, '"ny" sound'),           # ɲ
#     Consonant(232, 'cy',  'palatal',    'stop',         0, '"cy" sound'),           # c
#     Consonant(233, 'gy',  'palatal',    'stop',         1, '"gy" sound'),           # ɟ
#     Consonant(234, 'ts',  'alveolar',   'affricate',    0, '"\'s" as in \'sup'),    # ts (Sibilant affricate)
#     Consonant(235, 'dz',  'alveolar',   'affricate',    1, '"dz" as in "adze" '),   # dz (Sibilant affricate)
#     Consonant(236, 'xh',  'velar',      'fricative',    0, '"ch" in Scottish "loch"'),      # x
#     Consonant(237, 'gh',  'velar',      'fricative',    1, '"gh" in Scottish "laghail"'),   # ɣ
#     Consonant(238, 'r~',  'alveolar',   'trill',        1, 'rolled "r"'),          # r
#     Consonant(239, 'b~',  'bilabial',   'trill',        1, 'rolled "b"'),          # B
#     Consonant(240, '\'',  'glottal',    'stop',         0, 'glottal stop, as in the middle sound of "uh-oh"')  # ʔ
#     ]


VOWELS = [

    # -- Monophthongs -- #
    Vowel(id_=101, char='i',  position=( (0, 7), ),  manner='lax',   lips='unrounded', description='short "i", as in "sit"'),     # /ɪ/
    Vowel(id_=102, char='e',  position=( (0, 9), ),  manner='tense', lips='unrounded', description='long "e", as in "see"'),      # /i(ː)/
    Vowel(id_=103, char='u',  position=( (5, 2), ),  manner='lax',   lips='unrounded', description='short "u", as in "up"'),      # /ʌ/
    Vowel(id_=114, char='e',  position=( (0, 5), ),  manner='lax',   lips='unrounded', description='short "e", as in "beg"'),     # /ɛ/
    Vowel(id_=105, char='a',  position=( (0, 2), ),  manner='lax',   lips='unrounded', description='short "a", as in "bad"'),     # /æ/
    Vowel(id_=107, char='aa', position=( (9, 1), ),  manner='tense', lips='unrounded', description='flat "a", as in "ah"'),       # /ɑ/
    Vowel(id_=110, char='oo', position=( (9, 7), ),  manner='lax',   lips='rounded',   description='short "u", as in "put"'),     # /ʊ/
    Vowel(id_=111, char='ue', position=( (9, 9), ),  manner='tense', lips='rounded',   description='long "u", as in "blue"'),     # /uː/
    Vowel(id_=112, char='au', position=( (9, 3), ),  manner='tense', lips='rounded',   description='"aw", as in "saw"'),          # /ɔ/

    # -- Diphthongs -- #
    Vowel(id_=106, char='ae', position=( (0, 5), (3, 7) ),  manner='tense', lips='unrounded', description='long "a", as in "gate"'),  # eɪ
    Vowel(id_=108, char='ie', position=( (3, 0), (4, 7) ),  manner='tense', lips='unrounded', description='long "i", as in "hide"'),  # äɪ
    Vowel(id_=109, char='o',  position=( (8, 5), (9, 7) ),  manner='tense', lips='rounded',   description='long "o", as in "toe"'),   # oʊ
    Vowel(id_=113, char='ou', position=( (5, 0), (5, 6) ),  manner='tense', lips='unrounded', description='"ou", as in "out"'),       # aʊ
    Vowel(id_=114, char='oi', position=( (9, 4), (5, 7) ),  manner='tense', lips='unrounded', description='"oi", as in "toil"'),      # ɔɪ
    Vowel(id_=115, char='eo', position=( (0, 7), (9, 7) ),  manner='tense', lips='unrounded', description='"eo", as in "beorn"')      # eo
    # Source: https://en.wikipedia.org/wiki/Diphthong#English
    # leer   ɪɚ 
    # lair   ɛɚ
    # lure   ʊɚ
]

ID_TO_PHONEME = {phoneme.id_: phoneme for phoneme in itertools.chain(CONSONANTS, VOWELS)}


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
                                Rule('any', 'approximant', 'any', [222, 223]) ),
    # spl
    # PClusterGenerator( Rule('alveolar', 'fricative', 0, []),
    #                    Rule('any', 'plosive', 0, [203, 205]),
    #                    Rule('any', 'lateral', 'any', [222, 223]) )
    # ---------------------------------------------------------- #
    
    PClusterGenerator( 'onset', Rule('palatal',  'nasal',     0, []) ),  # ɲ̊
    PClusterGenerator( 'onset', Rule('palatal',  'nasal',     1, []) ),  # ɲ
    PClusterGenerator( 'onset', Rule('palatal',  'stop',      0, []) ),  # c
    PClusterGenerator( 'onset', Rule('palatal',  'stop',      1, []) ),  # ɟ
    PClusterGenerator( 'onset', Rule('alveolar', 'affricate', 0, []) ),  # ts
    PClusterGenerator( 'onset', Rule('alveolar', 'affricate', 1, []) ),  # dz
    PClusterGenerator( 'onset', Rule('velar',    'fricative', 0, []) ),  # x
    PClusterGenerator( 'onset', Rule('velar',    'fricative', 1, []) ),  # ɣ
    PClusterGenerator( 'onset', Rule('alveolar', 'trill',     1, []) ),  # r
    PClusterGenerator( 'onset', Rule('bilabial', 'trill',     1, []) ),  # B
    # PClusterGenerator( 'onset', Rule('glottal',  'stop',      0, []) )   # ʔ
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
                               Rule('dental', 'fricative', 0, []) ),


    PClusterGenerator( 'onset', Rule('alveolar', 'affricate', 0, []) ),  # ts
    PClusterGenerator( 'onset', Rule('alveolar', 'affricate', 1, []) ),  # dz
    PClusterGenerator( 'onset', Rule('velar',    'fricative', 0, []) ),  # x
    PClusterGenerator( 'onset', Rule('velar',    'fricative', 1, []) ),  # ɣ
    PClusterGenerator( 'onset', Rule('alveolar', 'trill',     1, []) ),  # r
    PClusterGenerator( 'onset', Rule('bilabial', 'trill',     1, []) )  # B
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


