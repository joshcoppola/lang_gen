# coding=Latin-1

from __future__ import division
from random import randint as roll
import random
from collections import defaultdict

from lang_gen import weighted_random, chance


## Vowels: English mapping
# 101	i		sit		|	102	ee		see
# 103	u		up		|	104	e		beg
# 105	a		bad		|	106	ae		sundae
# 107	aa		Saab	|	108	ie		pie
# 109	oe		toe		|	110	oo		good
# 111	ue		blue	|	112	au		auger
# 113	ou		out		|	114	oi		toil


## ASCI nums for characters with accents
#128 Ç 135 ç
#144 É			130 é 136 ê 137 ë 138 è
#142 Ä 143 Å	131 â 132 ä 133 à 134 å 160 á
#				139 ï 140 î 141 ì 161 í
#153 Ö			147 ô 148 ö 149 ò 162 ó
#154 Ü			129 ü 150 û 151 ù 163 ú
#146 Æ			145 æ
#152 ÿ
#165 Ñ			164 ñ


### For these special characters, precompute the mapping into variables

# -- Vowels -- #

e_r = chr(130) # é  r = right accent
e_l = chr(138) # è  l = left accent
e_c = chr(136) # ê  c = carrot
e_u = chr(137) # ë  u = umlaut
E_R = chr(144) # É  

a_r = chr(160) # á
a_l = chr(133) # à
a_c = chr(131) # â
a_u = chr(132) # ä
a_o = chr(134) # å  o = little circle thing
A_U = chr(142) # Ä 
A_O = chr(143) # Å

i_r = chr(161) # í 
i_l = chr(141) # ì
i_c = chr(140) # î
i_u = chr(139) # ï

o_r = chr(162) # ó
o_l = chr(149) # ò
o_c = chr(147) # ô
o_u = chr(148) # ö
O_U = chr(153) # Ö

u_r = chr(163) # ú
u_l = chr(151) # ù
u_c = chr(150) # û
u_u = chr(129) # ü
U_U = chr(154) # Ü

ae = chr(145)  # æ
AE = chr(146)  # Æ

y_u = chr(152) # ÿ

# -- Consonants -- #

c_s = chr(135) # ç  s = squiggle
C_S = chr(128) # Ç

n_s = chr(164) # ñ
N_S = chr(165) # Ñ  

# -- Other symbols -- ##
sigma = chr(235)
strange_f = chr(159)



## Groups of symbols

RIGHT_ACCENTS = {
    a_r:(105, 106, 107),
    e_r:(102, 104),
    i_r:(101, 102, 108),
    o_r:(109, ), 
    u_r:(103, 110, 111)
}

LEFT_ACCENTS =  {
    a_l:(105, 106, 107),
    e_l:(102, 104),
    i_l:(101, 102, 108),
    o_l:(109, ), 
    u_l:(103, 110, 111)
}

CARROTS = {
    a_c:(105, 106, 107),
    e_c:(102, 104),
    i_c:(101, 108), # 102:i_c
    o_c:(109, ), 
    u_c:(103, 110, 111),
}

UMLAUTS = {
    a_u:(105, 106, 107),
    e_u:(102, 104),
    i_u:(101, 108), # 102:i_u
    o_u:(109, ), 
    u_u:(103, 110, 111),
}



## A way to capitalize those ASCII characters with accents (not handled by regular python .capitalize() method)
SYMB_TO_CAPITAL = {
    i_u: 'I',  i_c: 'I',  i_l: 'I',  i_r: 'I',
    e_r: E_R,  e_c: 'E',  e_u: 'E',  e_l: E_R,
    u_u: U_U,  u_c: 'U',  u_l: 'U',  u_r: 'U',
    ae:  AE,   a_c: 'A',  a_u: A_U,  a_l: 'A',  a_o: A_O,  a_r: 'A',
    o_c: 'O',  o_u: O_U,  o_l: 'O',  o_r: 'O',
    y_u: 'Y',
    c_s: C_S,
    n_s: N_S
}


class Glyph:
    def __init__(self, phoneme_id, normal, before_consonant=None, after_consonant=None, at_beginning=None, at_end=None):
        self.phoneme_id = phoneme_id

        self.normal = normal

        # The glyph can change depending on its position in the word; this setup handles that
        self.before_consonant = before_consonant if before_consonant is not None else normal
        self.after_consonant  = after_consonant  if after_consonant  is not None else normal
        self.at_beginning     = at_beginning     if at_beginning     is not None else normal
        self.at_end           = at_end           if at_end           is not None else normal

         

    def get_glyph(self, position_info):
        ''' Get glyph depending on position in the word '''

        if   position_info['before_consonant']:  return self.before_consonant
        elif position_info['after_consonant']:   return self.after_consonant
        elif position_info['at_beginning']:      return self.at_beginning
        elif position_info['at_end']:            return self.at_end 
        else:                                    return self.normal


# In orthography step, each vowel phoneme can be translated to one of these possibilities
# In orthography step, each consonant phoneme can be translated to one of these possibilities

PHONEMES_WRITTEN = {

    # ----------- VOWELS ----------- #

    101: Glyph(101, 'i'), # sit
    102: Glyph(102, 'e'), # see      'ea'
    103: Glyph(103, 'u'), # up
    104: Glyph(104, 'e'), # beg
    105: Glyph(105, 'a'), # bad
    106: Glyph(106, 'a', at_end='ay'), # sundae   'ae'
    107: Glyph(107, 'a'), # Saab     'aa'
    108: Glyph(108, 'i', at_end='y'), # pie      'ie'
    109: Glyph(109, 'o'), # toe
    110: Glyph(110, 'u'), # good      'eu'  'eo'
    111: Glyph(111, 'u'), # blue      'ue'
    112: Glyph(112, 'a', at_end='aw'), # saw
    113: Glyph(113, 'ou'), # out
    114: Glyph(114, 'oi', at_end='oy'), # toil

    115: Glyph(115, 'eo'), # beorn
    
    # ----------- Consonants ----------- #

    201: Glyph(201, 'p'),   #
    202: Glyph(202, 'b'),   #
    203: Glyph(203, 't'),   #
    204: Glyph(204, 'd'),   #
    205: Glyph(205, 'k'),   # 'c'
    206: Glyph(206, 'g'),   #
    207: Glyph(207, 'ch'),   # c_s
    208: Glyph(208, 'j', at_end='ge'),   # 'g'
    209: Glyph(209, 'f'),   # 'ph'
    210: Glyph(210, 'v', at_end='ve'),
    211: Glyph(211, 'th'),
    212: Glyph(212, 'th'),   # dh
    213: Glyph(213, 's'),
    214: Glyph(214, 'z'),
    215: Glyph(215, 'sh'),   # x,
    216: Glyph(216, 'sh'),   # x,
    217: Glyph(217, 'h'),
    218: Glyph(218, 'm'),   #
    219: Glyph(219, 'n'),   #
    220: Glyph(220, 'ng'),   # chr(237) chr(238)
    221: Glyph(221, 'r'),
    222: Glyph(222, 'y'),
    223: Glyph(223, 'w'),
    224: Glyph(224, 'l'),


    230: Glyph(230, n_s),  # kn, cn
    231: Glyph(231, n_s),  # gn,
    232: Glyph(232, 'cy', before_consonant='c'),  # c_s
    233: Glyph(233, 'gy', before_consonant='g'),  # c_s
    234: Glyph(234, 'ts', before_consonant='s\''),
    235: Glyph(235, 'dz', before_consonant='z\''),
    236: Glyph(236, 'ch', after_consonant='h'),  # xh, ch, x c_s
    237: Glyph(237, 'gh', after_consonant='h'),  # c_s
    238: Glyph(238, 'r'),
    239: Glyph(239, 'b'),
    240: Glyph(240, '\''),

    251: Glyph(251, 'ph', before_consonant='p'), # p    p'
    252: Glyph(252, 'bh', before_consonant='b'), # b    b'
    253: Glyph(253, 'th', before_consonant='t'), # t    t'
    254: Glyph(254, 'dh', before_consonant='d'), # d    d'
    255: Glyph(255, 'kh', before_consonant='k'), # k q  k'
    256: Glyph(256, 'gh', before_consonant='g'), # g    g'

    300: Glyph(300, ''), # (300 and 301 are special - used at syllable onsets which don't start with
    301: Glyph(301, ''), # a consonant and syllable codas which don't end with a consonant, respectively

    }

PHONEMES_BY_GLYPH = defaultdict(list)

for phoneme_id, glyph in PHONEMES_WRITTEN.iteritems():
    PHONEMES_BY_GLYPH[glyph.normal].append(phoneme_id)



class Orthography:
    ''' Class to map phonemes to letters. Very shallow at the moment '''
    def __init__(self, parent_language, parent_orthography=None):

        self.parent_language = parent_language
        # The parent orthography this one is descended from, if any
        self.parent_orthography = parent_orthography
        # A list of languages which can be written in this orthography
        self.languages = []

        self.syllable_division = None

        ## ------------------ Consonants -------------------- ##

        glyph_bank = {'q', 'c', 'x', c_s, 'ph', 'dh', 'cn', 'kn', 'gn'}
        used_apostrophe = 0

        # Allow specification of any symbols that are predefined
        self.mapping = {phoneme: PHONEMES_WRITTEN[phoneme] for phoneme in PHONEMES_WRITTEN}

        # aspirated_plosives = self.parent_language.get_matching_consonants(method='plosive', special='aspirated')
        # unaspirated_plosives = self.parent_language.get_matching_consonants(method='plosive', special=None)

        if chance(15):
            self.syllable_division = '-'

        # Potentially replace aspirated plosives with an apostrophe after it's name
        if chance(15) and not self.syllable_division:
            # used_apostrophe = 1
            self.mapping[251] = Glyph(251, 'p\'', before_consonant='p', at_end='p')  # ph
            self.mapping[252] = Glyph(252, 'b\'', before_consonant='b', at_end='b')  # bh
            self.mapping[253] = Glyph(253, 't\'', before_consonant='t', at_end='t')  # th
            self.mapping[254] = Glyph(254, 'd\'', before_consonant='d', at_end='d')  # dh
            self.mapping[255] = Glyph(255, 'k\'', before_consonant='k', at_end='k')  # kh
            self.mapping[256] = Glyph(256, 'g\'', before_consonant='g', at_end='g')  # gh

        if 'c' in glyph_bank and chance(40):
            glyph_bank.remove('c')
            self.mapping[205] = Glyph(205, 'c')

        # -------- /ny/ phoneme ------- #
        if chance(35):
            self.mapping[230] = Glyph(230, 'kn', after_consonant='n', at_end='n') # cn
            self.mapping[231] = Glyph(231, 'gn', after_consonant='n', at_end='n') #
        
        if chance(15):
            self.mapping[230] = Glyph(230, 'nh', after_consonant='n', at_end='n') 
            self.mapping[231] = Glyph(231, 'nh', after_consonant='n', at_end='n') 
        # ------------------------------ #

        if chance(35):
            self.mapping[232] = Glyph(232, c_s) #  cy
            self.mapping[233] = Glyph(233, c_s) #  gy

        if chance(45):
            self.mapping[236] = Glyph(236, 'x', after_consonant='h') # ch, x c_s  xh
        elif chance(35):
            self.mapping[236] = Glyph(236, 'ch', after_consonant='h')
            # self.mapping[237] =  # c_s  gh

        if chance(25):
            self.mapping[215] = Glyph(215, 'x')
            self.mapping[216] = Glyph(216, 'x')


        if chance(25):
            self.mapping[212] = Glyph(212, 'dh') # th

        # Chance of language putting placeholders where missing onsets / codas go
        if chance(10) and not self.syllable_division:
            # (300 and 301 are special - used at syllable onsets which don't start with
            # a consonant and syllable codas which don't end with a consonant, respectively
            self.mapping[300] = Glyph(300, '-', before_consonant='', at_beginning='', at_end='') 
            self.mapping[301] = Glyph(301, '-', before_consonant='', at_beginning='', at_end='') 

        # Chance to give some variation to the "r" letter
        if chance(35):
            self.mapping[221].at_beginning = 'rh'
        if chance(25) and not self.syllable_division:
            self.mapping[221].normal = 'rr'

        # Chance to give some variation to the "l" letter
        if chance(5):
            self.mapping[224].at_beginning = 'lh'
        if chance(5):
            self.mapping[224].at_end = 'll'
        if chance(15 and not self.syllable_division):
            self.mapping[224].normal = 'll'

        # Some variation for the "m" and "n" letters
        if chance(15) and not self.syllable_division:
            self.mapping[218].normal = 'mm'
        if chance(15) and not self.syllable_division:
            self.mapping[219].normal = 'nn'
        

        ## ------------------ Vowels -------------------- ##


        if chance(85):
            diacritic_types = ['left_accent', 'right_accent', 'carrot', 'umlaut']
            chosen_types = []

            number_of_diacritics = random.choice((1, 2, 2, 2, 3))

            for _ in xrange(number_of_diacritics):
                diacritic = diacritic_types.pop(random.randrange(len(diacritic_types)))
                chosen_types.append(diacritic)

            if 'left_accent'  in chosen_types:  self.apply_diacritic_type(diacritic_dict=LEFT_ACCENTS)
            if 'right_accent' in chosen_types:  self.apply_diacritic_type(diacritic_dict=RIGHT_ACCENTS)
            if 'carrot'       in chosen_types:  self.apply_diacritic_type(diacritic_dict=CARROTS)
            if 'umlaut'       in chosen_types:  self.apply_diacritic_type(diacritic_dict=UMLAUTS)

        ## Sort of silly, but it we allow "y" to be used in place of "i", we need
        ## to make sure that "y" cannot also be a consonant (we'll replace with J for now)
        if chance(5):
            y_vowel = random.choice(('y', y_u))
            self.mapping[101] = Glyph(101, y_vowel)
            self.mapping[108] = Glyph(108, y_vowel)
            # Swap the 'y' consonant with a 'j'
            self.mapping[222] = Glyph(222, 'j')
            

        # # Replace "th" with "thorn"/"eth" (sigma symbol in our library)
        # if roll(0, 15) == 1:
        #     self.replace_grapheme(phoneme_num=211, old='clear_all', new=sigma, new_prob=1)
        #     self.replace_grapheme(phoneme_num=212, old='clear_all', new=sigma, new_prob=1)
    
        # # Use ƒ instead of sh
        # if roll(0, 15) == 1:
        #     self.replace_grapheme(phoneme_num=215, old='sh', new=strange_f, new_prob=1)
        #     self.replace_grapheme(phoneme_num=216, old='zh', new=strange_f, new_prob=1)

    def apply_diacritic_type(self, diacritic_dict):
        ''' Simple way to sprinkle in some diacritics into the vowels '''
        for letter, phoneme_ids in diacritic_dict.iteritems():
            for phoneme_id in phoneme_ids:
                if chance(1, top=len(phoneme_ids)):
                    self.mapping[phoneme_id] = Glyph(phoneme_id=phoneme_id, normal=letter)

    def get_alphabet(self):
        ''' Print out the alphabet for this language '''
        alphabet = sorted([glyph.normal for glyph in self.mapping.values()])

        for glyph in alphabet:
            print glyph


    def phon_to_orth(self, word):
        ''' Convert a sequence of phoneme ids to a string, based on the orthography of this language '''
        orth = ''

        # Go through each phonoeme id in the sequence and find the glyph
        for phoneme_id, position_info in word.get_phonemes():
            # Some orthographies put a boundary marker between syllables
            if self.syllable_division and position_info['is_boundary_between_syllables']:
                orth += self.syllable_division
            # Grab the glyph, based on its position in the word
            orth += self.mapping[phoneme_id].get_glyph( position_info )

        return orth



