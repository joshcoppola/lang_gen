# coding=Latin-1

from random import randint as roll

from lang_gen import weighted_random


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

# In orthography step, each vowel phoneme can be translated to one of these possibilities
# In orthography step, each consonant phoneme can be translated to one of these possibilities

PHONEMES_WRITTEN = {

    # ----------- VOWELS ----------- #

    101:'i',  # sit
    102:'e',  # see      'ea'
    103:'u',  # up
    104:'e',  # beg
    105:'a',  # bad
    106:'a',  # sundae   'ae'
    107:'a',  # Saab     'aa'
    108:'i',  # pie      'ie'
    109:'o',  # toe
    110:'u',  # good      'eu'  'eo'
    111:'u',  # blue      'ue'
    112:'au', # auger
    113:'ou', # out
    114:'oi', # toil

    # ----------- Consonants ----------- #

    300:'', # (300 and 301 are special - used at syllable onsets which don't start with
    301:'', # a consonant and syllable codas which don't end with a consonant, respectively

    201:'p',
    202:'b',
    203:'t',
    204:'d',
    205:'k',  # 'q' 'c'
    206:'g',
    207:'ch', # 'c' c_s
    208:'j',  # 'g'
    209:'f',  # 'ph'
    210:'v',
    211:'th',
    212:'th',
    213:'s',
    214:'z',
    215:'sh',
    216:'zh', # 'z' c_s
    217:'h',
    218:'m',
    219:'n',
    220:'ng', # chr(237) chr(238)
    221:'r',
    222:'y',
    223:'w',
    224:'l'
    }



class Orthography:
    ''' Class to map phonemes to letters. Very shallow at the moment '''
    def __init__(self, parent_orthography=None):
        # The parent orthography this one is descended from, if any
        self.parent_orthography = parent_orthography
        # A list of languages which can be written in this orthography
        self.languages = []
        
        # Allow specification of any symbols that are predefined
        self.mapping = {}

        # Making copies of the possible written vowel representations, to be modified here
        self.unproc_mapping = {phoneme: PHONEMES_WRITTEN[phoneme] for phoneme in PHONEMES_WRITTEN}


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


    def phon_to_orth(self, phoneme_sequence):

        orth = ''

        for p in phoneme_sequence:
            orth += PHONEMES_WRITTEN[p]


        print orth



