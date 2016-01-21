# coding=Latin-1

from lang_gen import weighted_choice


## Vowels: English mapping
# 101	i		sit		|	102	ee		see
# 103	u		up		|	104	e		beg
# 105	a		bad		|	106	ae		sundae
# 107	aa		Saab	|	108	ie		pie
# 109	oe		toe		|	110	oo		good
# 111	ue		blue	|	112	au		auger
# 113	ou		out		|	114	oi		toil


## ASCI nums for characters with accents
#128 � 135 �
#144 �			130 � 136 � 137 � 138 �
#142 � 143 �	131 � 132 � 133 � 134 � 160 �
#				139 � 140 � 141 � 161 �
#153 �			147 � 148 � 149 � 162 �
#154 �			129 � 150 � 151 � 163 �
#146 �			145 �
#152 �
#165 �			164 �


### For these special characters, precompute the mapping into variables

# -- Vowels -- #

e_r = chr(130) # �  r = right accent
e_l = chr(138) # �  l = left accent
e_c = chr(136) # �  c = carrot
e_u = chr(137) # �  u = umlaut
E_R = chr(144) # �  

a_r = chr(160) # �
a_l = chr(133) # �
a_c = chr(131) # �
a_u = chr(132) # �
a_o = chr(134) # �  o = little circle thing
A_U = chr(142) # � 
A_O = chr(143) # �

i_r = chr(161) # � 
i_l = chr(141) # �
i_c = chr(140) # �
i_u = chr(139) # �

o_r = chr(162) # �
o_l = chr(149) # �
o_c = chr(147) # �
o_u = chr(148) # �
O_U = chr(153) # �

u_r = chr(163) # �
u_l = chr(151) # �
u_c = chr(150) # �
u_u = chr(129) # �
U_U = chr(154) # �

ae = chr(145)  # �
AE = chr(146)  # �

y_u - chr(152) # �

# -- Consonants -- #

c_s = chr(135) # �  s = squiggle
C_S = chr(128) # �

n_s = chr(164) # �
N_S = chr(165) # �  


## A way to capitalize those ASCII characters with accents (not handled by regular python .capitalize() method)
SYMB_TO_CAPITAL = {chr(139):'I', chr(140):'I', chr(141):'I', chr(161):'I',
                    chr(130):chr(144), chr(136):'E', chr(137):'E', chr(138):chr(144), chr(141):'I', chr(161):'I',
                    chr(129):chr(154), chr(150):'U', chr(151):'U', chr(163):'U',
                    chr(145):chr(146),  chr(131):'A', chr(132):chr(142), chr(133):'A', chr(134):chr(143), chr(160):'A',
                    chr(147):'O', chr(148):chr(153), chr(149):'O', chr(162):'O',
                    chr(152):'Y',
                    chr(135):chr(128),
                    chr(164):chr(165)
                    }

# In orthography step, each vowel phoneme can be translated to one of these possibilities
# In orthography step, each consonant phoneme can be translated to one of these possibilities

PHONEMES_WRITTEN = {
# ----------- VOWELS ----------- #
    101:{'i':3, chr(139):1, chr(140):1, chr(141):1, chr(161):1},
    102:{'e':2, 'ea':2, chr(130):1, chr(136):1, chr(137):1, chr(138):1, chr(141):1, chr(161):1},
    103:{'u':3, chr(129):1, chr(150):1, chr(151):1, chr(163):1},
    104:{'e':3, chr(130):1, chr(136):1, chr(137):1, chr(138):1},
    105:{'a':3, chr(145):1,  chr(131):1, chr(132):1, chr(133):1, chr(134):1, chr(160):1},
    106:{'ae':3, chr(131):1, chr(132):1, chr(133):1, chr(134):1, chr(160):1},
    107:{'a':2, 'aa':2, chr(131):1, chr(132):1, chr(133):1, chr(134):1, chr(160):1},
    108:{'ie':1, 'i':1, chr(139):1, chr(140):1, chr(141):1, chr(161):1},
    109:{'o':1, chr(147):1, chr(148):1, chr(149):1, chr(162):1},
    110:{'u':1, 'eu':2, 'eo':2, chr(129):1, chr(150):1, chr(151):1, chr(163):1},
    111:{'ue':2, chr(129):1, chr(150):1, chr(151):1, chr(163):1},
    112:{'au':1},
    113:{'ou':1},
    114:{'oi':1},

# ----------- Consonants ----------- #
# (300 and 301 are special - used at syllable onsets which don't start with a consonant and
# syllable codas which don't end with a consonant, respectively
    300:{'':1},
    301:{'':1},

    201:{'p':1},
    202:{'b':1},
    203:{'t':1},
    204:{'d':1},
    205:{'k':4, 'q':1, 'c':2},
    206:{'g':1},
    207:{'ch':15, 'c':3, chr(135):1},
    208:{'j':1, 'g':1},
    209:{'f':4, 'ph':1},
    210:{'v':1},
    211:{'th':1},
    212:{'th':1},
    213:{'s':1},
    214:{'z':1},
    215:{'sh':1},
    216:{'zh':1, 'z':2, chr(135):1},
    217:{'h':1},
    218:{'m':1},
    219:{'n':1},
    220:{'ng':2, chr(237):1, chr(238):1},
    221:{'r':1},
    222:{'y':1},
    223:{'w':1},
    224:{'l':1}
    }



class Orthography:
    ''' Class to map phonemes to letters. Very shallow at the moment '''
    def __init__(self, possible_vowels, possible_consonants, nordic_i=0, use_weird_symbols=0):
        # Allow specification of any symbols that are predefined
        self.mapping = {}

        # Making copies of the possible written vowel representations, to be modified here
        self.unproc_mapping = {phoneme: PHONEME_WRITTEN[phoneme] for phoneme in PHONEME_WRITTEN}


        ## Sort of silly, but it we allow "y" to be used in place of "i", we need
        ## to make sure that "y" cannot also be a consonant (we'll replace with J for now)
        if nordic_i:
            self.unproc_mapping[101] = {'y':1, chr(152):1}
            self.unproc_mapping[108] = {'y':1, chr(152):1}
            # Swap the 'y' consonant with a 'j'
            self.unproc_mapping[222] = {'j':1}

        # Replace "th" with "thorn"/"eth" (sigma symbol in our library)
        if roll(0, 15) == 1:
            self.replace_grapheme(phoneme_num=211, old='clear_all', new=chr(235), new_prob=1)
            self.replace_grapheme(phoneme_num=212, old='clear_all', new=chr(235), new_prob=1)
    
        # Use � instead of sh
        if roll(0, 15) == 1:
            self.replace_grapheme(phoneme_num=215, old='sh', new=chr(159), new_prob=1)
            self.replace_grapheme(phoneme_num=216, old='zh', new=chr(159), new_prob=1)


        ## TODO ## 
        # Should run through the full unproc_mapping and add default mapping for phonemes
        # not in this orthography's parent language, so that any foreign words translated
        # can be suitably recognizeable 

        # Here's where consonants get mapped
        for phoneme_num, graphemes_and_probs in self.unproc_mapping.iteritems():
            # Pick a grapheme to represent this phoneme via weighted choice 
            grapheme = weighted_choice(graphemes_and_probs)
            # Apply it to our mapping dict
            self.mapping[phoneme_num] = grapheme

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

