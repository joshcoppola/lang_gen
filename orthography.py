# coding=Latin-1

from __future__ import division
from random import randint as roll

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
    i_u:'I',  i_c:'I',  i_l:'I',  i_r:'I',
    e_r:E_R,  e_c:'E',  e_u:'E',  e_l:E_R,
    u_u:U_U,  u_c:'U',  u_l:'U',  u_r:'U',
    ae:AE,    a_c:'A',  a_u:A_U,  a_l:'A',  a_o:A_O,  a_r:'A',
    o_c:'O',  o_u:O_U,  o_l:'O',  o_r:'O',
    y_u:'Y',
    c_s:C_S,
    n_s:N_S
}


class Glyph:
    def __init__(self, phoneme_id, normal, after_consonant):
        self.phoneme_id = phoneme_id

        self.normal = normal
        self.after_consonant = after_consonant

    def get_glyph(self, after_consonant):
        if after_consonant:
            return self.after_consonant

        else:
            return self.normal



# In orthography step, each vowel phoneme can be translated to one of these possibilities
# In orthography step, each consonant phoneme can be translated to one of these possibilities

PHONEMES_WRITTEN = {

    # ----------- VOWELS ----------- #

    101: Glyph(101, 'i',  'i' ), # sit
    102: Glyph(102, 'e',  'e' ), # see      'ea'
    103: Glyph(103, 'u',  'u' ), # up
    104: Glyph(104, 'e',  'e' ), # beg
    105: Glyph(105, 'a',  'a' ), # bad
    106: Glyph(106, 'a',  'a' ), # sundae   'ae'
    107: Glyph(107, 'a',  'a' ), # Saab     'aa'
    108: Glyph(108, 'i',  'i' ), # pie      'ie'
    109: Glyph(109, 'o',  'o' ), # toe
    110: Glyph(110, 'u',  'u' ), # good      'eu'  'eo'
    111: Glyph(111, 'u',  'u' ), # blue      'ue'
    112: Glyph(112, 'a',  'a' ), # saw
    113: Glyph(113, 'ou', 'ou'), # out
    114: Glyph(114, 'oi', 'oi'), # toil

    115: Glyph(115, 'eo', 'eo'), # beorn
    
    # ----------- Consonants ----------- #

    300: Glyph(300, '',   ''), # (300 and 301 are special - used at syllable onsets which don't start with
    301: Glyph(301, '',   ''), # a consonant and syllable codas which don't end with a consonant, respectively

    201: Glyph(201, 'p',  'p'),   #
    202: Glyph(202, 'b',  'b'),   #
    203: Glyph(203, 't',  't'),   #
    204: Glyph(204, 'd',  'd'),   #
    205: Glyph(205, 'k',  'k'),   # 'c'
    206: Glyph(206, 'g',  'g'),   #
    207: Glyph(207, 'ch', 'ch'),   # c_s
    208: Glyph(208, 'j',  'j'),   # 'g'
    209: Glyph(209, 'f',  'f'),   # 'ph'
    210: Glyph(210, 'v',  'v'),
    211: Glyph(211, 'th', 'th'),
    212: Glyph(212, 'th', 'th'),   # dh
    213: Glyph(213, 's',  's'),
    214: Glyph(214, 'z',  'z'),
    215: Glyph(215, 'sh', 'sh'),   # x,
    216: Glyph(216, 'sh', 'sh'),   # x,
    217: Glyph(217, 'h',  'h'),
    218: Glyph(218, 'm',  'm'),   #
    219: Glyph(219, 'n',  'n'),   #
    220: Glyph(220, 'ng', 'ng'),   # chr(237) chr(238)
    221: Glyph(221, 'r',  'r'),
    222: Glyph(222, 'y',  'y'),
    223: Glyph(223, 'w',  'w'),
    224: Glyph(224, 'l',  'l'),


    230: Glyph(230, n_s,  n_s),  # kn, cn
    231: Glyph(231, n_s,  n_s),  # gn,
    232: Glyph(232, 'cy', 'c'),  # c_s
    233: Glyph(233, 'gy', 'g'),  # c_s
    234: Glyph(234, 'ts', 's\''),
    235: Glyph(235, 'dz', 'z\''),
    236: Glyph(236, 'ch', 'h'),  # xh, ch, x c_s
    237: Glyph(237, 'gh', 'h'),  # c_s
    238: Glyph(238, 'r',  'r'),
    239: Glyph(239, 'b',  'b'),
    240: Glyph(240, '\'', '\''),

    251: Glyph(251, 'ph', 'p'), # p    p'
    252: Glyph(252, 'bh', 'b'), # b    b'
    253: Glyph(253, 'th', 't'), # t    t'
    254: Glyph(254, 'dh', 'd'), # d    d'
    255: Glyph(255, 'kh', 'k'), # k q  k'
    256: Glyph(256, 'gh', 'g'), # g    g'
    }


class Orthography:
    ''' Class to map phonemes to letters. Very shallow at the moment '''
    def __init__(self, parent_language, parent_orthography=None):

        self.parent_language = parent_language
        # The parent orthography this one is descended from, if any
        self.parent_orthography = parent_orthography
        # A list of languages which can be written in this orthography
        self.languages = []



        ## ------------------ Consonants -------------------- ##

        glyph_bank = {'q', 'c', 'x', c_s, 'ph', 'dh', 'cn', 'kn', 'gn'}
        used_apostrophe = 0

        # Allow specification of any symbols that are predefined
        self.mapping = {phoneme: PHONEMES_WRITTEN[phoneme] for phoneme in PHONEMES_WRITTEN}

        # aspirated_plosives = self.parent_language.get_matching_consonants(method='plosive', special='aspirated')
        # unaspirated_plosives = self.parent_language.get_matching_consonants(method='plosive', special=None)

        # Potentially replace aspirated plosives with an apostrophe after it's name
        if chance(15):
            # used_apostrophe = 1
            self.mapping[251] = Glyph(251, 'p\'', 'p')  # ph
            self.mapping[252] = Glyph(252, 'b\'', 'b')  # bh
            self.mapping[253] = Glyph(253, 't\'', 't')  # th
            self.mapping[254] = Glyph(254, 'd\'', 'd')  # dh
            self.mapping[255] = Glyph(255, 'k\'', 'k')  # kh
            self.mapping[256] = Glyph(256, 'g\'', 'g')  # gh

        if 'c' in glyph_bank and chance(40):
            glyph_bank.remove('c')
            self.mapping[205] = Glyph(205, 'c', 'c')

        if chance(35):
            self.mapping[230] = Glyph(230, 'kn', 'n') # cn
            self.mapping[231] = Glyph(231, 'gn', 'n') #

        if chance(35):
            self.mapping[232] = Glyph(232, c_s, c_s) #  cy
            self.mapping[233] = Glyph(233, c_s, c_s) #  gy

        if chance(45):
            self.mapping[236] = Glyph(236, 'x', 'h') # ch, x c_s  xh
        elif chance(35):
            self.mapping[236] = Glyph(236, 'ch', 'h')
            # self.mapping[237] =  # c_s  gh

        if chance(25):
            self.mapping[215] = Glyph(215, 'x', 'x')
            self.mapping[216] = Glyph(216, 'x', 'x')


        if chance(25):
            self.mapping[212] = Glyph(212, 'dh', 'dh') # th


        ## ------------------ Vowels -------------------- ##


            



        ## Sort of silly, but it we allow "y" to be used in place of "i", we need
        ## to make sure that "y" cannot also be a consonant (we'll replace with J for now)
        # if roll(1, 15) == 1:
        #     self.unproc_mapping[101] = {'y':1, y_u:1}
        #     self.unproc_mapping[108] = {'y':1, y_u:1}
        #     # Swap the 'y' consonant with a 'j'
        #     self.unproc_mapping[222] = {'j':1}

        # # Replace "th" with "thorn"/"eth" (sigma symbol in our library)
        # if roll(0, 15) == 1:
        #     self.replace_grapheme(phoneme_num=211, old='clear_all', new=sigma, new_prob=1)
        #     self.replace_grapheme(phoneme_num=212, old='clear_all', new=sigma, new_prob=1)
    
        # # Use ƒ instead of sh
        # if roll(0, 15) == 1:
        #     self.replace_grapheme(phoneme_num=215, old='sh', new=strange_f, new_prob=1)
        #     self.replace_grapheme(phoneme_num=216, old='zh', new=strange_f, new_prob=1)


        ## TODO ## 
        # Should run through the full unproc_mapping and add default mapping for phonemes
        # not in this orthography's parent language, so that any foreign words translated
        # can be suitably recognizeable 

        # Here's where consonants get mapped
        # for phoneme_num, graphemes_and_probs in self.unproc_mapping.iteritems():
        #     # Pick a grapheme to represent this phoneme via weighted choice 
        #     grapheme = weighted_random(graphemes_and_probs)
        #     # Apply it to our mapping dict
        #     self.mapping[phoneme_num] = grapheme

    def replace_grapheme(self, phoneme_num, old, new, new_prob):
        ''' Replace an instance of a possible grapheme with a new possible grapheme '''
        # Id old is set to 'clear_all' clears all other grapheme options, so that there is no random chance of getting 
        # anything other than the specified new phoneme
        if old == 'clear_all':
            self.unproc_mapping[phoneme_num] = {}
        # Otherwise, remove the old grapheme from the possibilities, but retain the other possibilities
        else:
            del self.unproc_mapping[phoneme_num][old]

        # Add in the new grapheme and its probability into the mix
        self.unproc_mapping[phoneme_num][new] = new_prob


    def get_alphabet(self):

        alphabet = sorted([glyph.normal for glyph in self.mapping.values()])

        for glyph in alphabet:
            print glyph


    def phoneme_is_after_consonant(self, phoneme_sequence, current_index):

        if current_index > 0 and 200 <= phoneme_sequence[current_index-1] <= 299:
            return 1

        else:
            return 0

    def phon_to_orth(self, phoneme_sequence):

        orth = ''

        for i, phoneme_id in enumerate(phoneme_sequence):
            glyph = PHONEMES_WRITTEN[phoneme_id]

            after_consonant = self.phoneme_is_after_consonant(phoneme_sequence=phoneme_sequence, current_index=i)
            actual_glyph = glyph.get_glyph(after_consonant=after_consonant)

            orth += actual_glyph


        return orth



