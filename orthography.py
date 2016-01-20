# coding=Latin-1



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
VOWEL_WRITTEN = {101:['i', 'i', 'i', chr(139), chr(140), chr(141), chr(161)],
                102:['e', 'e', 'ea', 'ea', chr(130), chr(136), chr(137), chr(138), chr(141), chr(161)],
                103:['u', 'u', 'u', chr(129), chr(150), chr(151), chr(163)],
                104:['e', 'e', 'e', chr(130), chr(136), chr(137), chr(138)],
                105:['a', 'a', 'a', chr(145),  chr(131), chr(132), chr(133), chr(134), chr(160)],
                106:['ae', 'ae', 'ae', chr(131), chr(132), chr(133), chr(134), chr(160)],
                107:['a', 'a', 'aa', 'aa', chr(131), chr(132), chr(133), chr(134), chr(160)],
                108:['ie', 'i', 'i', chr(139), chr(140), chr(141), chr(161)],
                109:['o', chr(147), chr(148), chr(149), chr(162)],
                110:['u', 'eu', 'eu', 'eo', 'eo', chr(129), chr(150), chr(151), chr(163)],
                111:['ue', 'ue', chr(129), chr(150), chr(151), chr(163)],
                112:['au'],
                113:['ou'],
                114:['oi']
                }

# In orthography step, each consonant phoneme can be translated to one of these possibilities
# (300 and 301 are special - used at syllable onsets which don't start with a consonant and
# syllable codas which don't end with a consonant, respectively
CONSONANT_WRITTEN = {300:[''],
                    301:[''],

                    201:['p'],
                    202:['b'],
                    203:['t'],
                    204:['d'],
                    205:['k', 'k', 'k', 'k', 'q', 'c', 'c'],
                    206:['g'],
                    207:['ch', 'ch', 'ch', 'ch', 'c'],
                    208:['j', 'g'],
                    209:['f', 'f', 'f', 'f', 'ph'],
                    210:['v'],
                    211:['th'],
                    212:['th'],
                    213:['s'],
                    214:['z'],
                    215:['sh'],
                    216:['zh', 'z', 'z', chr(135)],
                    217:['h'],
                    218:['m'],
                    219:['n'],
                    220:['ng', 'ng', chr(237), chr(238)],
                    221:['r'],
                    222:['y'],
                    223:['w'],
                    224:['l']
                    }



class Orthography:
    ''' Class to map phonemes to letters. Very shallow at the moment '''
    def __init__(self, possible_vowels, possible_consonants, nordic_i=0, use_weird_symbols=0):
        # Allow specification of any symbols that are predefined
        self.mapping = {}

        # Making copies of the possible written vowel representations, to be modified here
        potential_v_rep = {}
        for vowel in possible_vowels:
            potential_v_rep[vowel] = VOWEL_WRITTEN[vowel][:]
        # Making copies of the possible written consonant representations, to be modified here
        potential_c_rep = {}
        for consonant in possible_consonants:
            potential_c_rep[consonant] = CONSONANT_WRITTEN[consonant][:]


        ## Sort of silly, but it we allow "y" to be used in place of "i", we need
        ## to make sure that "y" cannot also be a consonant (we'll replace with J for now)
        if nordic_i:
            if 101 in potential_v_rep:
                potential_v_rep[101] = ['y', chr(152)]
            if 108 in potential_v_rep:
                potential_v_rep[101] = ['y', chr(152)]

            potential_c_rep = self.replace_grapheme(mapping=potential_c_rep, phoneme=222, old='y', new='j')

        # If we want to (possibly) use non-english symbols in place of some of the consonants
        if (use_weird_symbols is None and roll(1, 5) == 1) or use_weird_symbols == 1:
            # Use "thorn"/"eth" (sigma symbol in our library)
            if roll(0, 1) == 1:
                potential_c_rep = self.replace_grapheme(mapping=potential_c_rep, phoneme=211, old='th', new=chr(235))
                potential_c_rep = self.replace_grapheme(mapping=potential_c_rep, phoneme=212, old='th', new=chr(235))
            # Use ç in place of ch
            if roll(0, 1) == 1:
                potential_c_rep = self.replace_grapheme(mapping=potential_c_rep, phoneme=207, old='ch', new=chr(135))
            # Use ƒ instead of sh
            if roll(0, 1) == 1:
                potential_c_rep = self.replace_grapheme(mapping=potential_c_rep, phoneme=215, old='sh', new=chr(159))
                potential_c_rep = self.replace_grapheme(mapping=potential_c_rep, phoneme=216, old='zh', new=chr(159))

            for i in WEIRD_CONS_LIST:
                if roll(1, 5) == 1:
                    cons = choice(potential_c_rep.keys())
                    # Make sure that the cons that's being replaced is not 'empty'
                    if cons < 300:
                        potential_c_rep[cons] = [i]

        # Here's where consonants get mapped
        for consonant, grapheme_list in potential_c_rep.iteritems():
            if not consonant in self.mapping:
                grapheme = choice(grapheme_list)
                self.mapping[consonant] = grapheme
        # Here's where vowels get mapped
        for vowel, grapheme_list in potential_v_rep.iteritems():
            if not vowel in self.mapping:
                grapheme = choice(grapheme_list)
                self.mapping[vowel] = grapheme

    def replace_grapheme(self, mapping, phoneme, old, new):
        ''' Replace an instance of a possible grapheme with a new possible grapheme '''
        if phoneme in mapping:
            num_graphemes = mapping[phoneme].count(old)
            for g in xrange(num_graphemes):
                mapping[phoneme].remove(old)
                mapping[phoneme].append(new)

            return mapping

        else:
            return mapping


