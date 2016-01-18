
from random import randint as roll
import random

from phonemes import CONSONANTS, VOWELS, POSSIBLE_ONSETS, POSSIBLE_CODAS

''' 
This file generates languages (and eventually orthographies) which have distinct
phonemes and orthographies.
'''


class Language:
    def __init__(self):
        self.onset_probabilities = {}
        self.coda_probabilities = {}
        self.vowel_probabilities_by_preceding_cluster = {}
        self.vowel_probabilities_by_following_cluster = {}

        self.vocabulary = {}
        self.orthography = None

    def generate_language_properties(self):
        # Start off by randomly discarding some phonemes that will never be used in this language
        unused_phonemes = []

        for c in CONSONANTS:
            if roll(1, 100) > 90:
                unused_phonemes.append(c)

        for v in VOWELS:
            if roll(1, 100) > 90 or v.type == 'diphthong':
                unused_phonemes.append(v)

        # Now, figure out probabilities for each of the onsets (assigning any containing forbidden phonemes to 0)
        for o in ALL_ONSETS:
            unused_phoneme = 0

            for onset_consonant in o.consonant_array:
                if onset_consonant not in unused_phonemes:
                    self.onset_probabilities[o] = 0
                    unused_phoneme = 1
                    break

            if unused_phoneme != 1:
                self.onset_probabilities[o] = roll(5, 45)

        for c in ALL_CODAS:
            unused_phoneme = 0
            for coda_consonant in c.consonant_array:
                if coda_consonant in unused_phonemes:
                    self.coda_probabilities[c] = 0
                    unused_phoneme = 1
                    break
                
            if unused_phoneme != 1:
                self.coda_probabilities[c] = roll(5, 45)

        # Set vowel probabilities, can vary on preceding and following cluster
        for v in VOWELS:
            # Vowel probabilities are hashes of cluster => probability values,
            # themselves stored by vowel. The overall hashes below look like
            # { {vowel ==> {cluster ==> prob}, {cluster ==> prob}, ...}, {vowel2:{ ... } }  }
            self.vowel_probabilities_by_preceding_cluster[v] = {}
            self.vowel_probabilities_by_following_cluster[v] = {}

            for (onset, probability) in self.onset_probabilities.iteritems():
                if v in unused_phonemes:
                    prob = 0
                else:
                    prob = random.choice([roll(0, 5), roll(20, 30), roll(50, 75)])
                
                self.vowel_probabilities_by_preceding_cluster[v][onset] = prob
            
            for (coda, p) in self.coda_probabilities.iteritems():
                if v in unused_phonemes:
                    prob = 0
                else:
                    prob = random.choice([roll(0, 5), roll(20, 30), roll(50, 75)])
                
                self.vowel_probabilities_by_following_cluster[v][coda] = prob 
            

    def create_word(self):
        onset = weighted_random(self.onset_probabilities)
        coda = weighted_random(self.coda_probabilities)
        vowel_probabilities = {}
        
        for v in VOWELS:
            onset_weight = self.vowel_probabilities_by_preceding_cluster[v][onset]
            coda_weight = self.vowel_probabilities_by_following_cluster[v][coda]

            vowel_probabilities[v] = onset_weight + coda_weight

        vowel = weighted_random(vowel_probabilities)
        #vowel = ['a', 'e', 'i', 'o', 'u'].sample
        print '{0}{1}{2}'.format(onset.get_string(), vowel.get_string(), coda.get_string())



def weighted_random(choices):
    ''' Naive algorithm. Input a hash of possibility+>weight, 
    where weight must be an integer for this to function 100% 
    correctly. Returns the choice '''
    total = 0
    for key, weight in choices.iteritems():
        total += weight

    choice_number = roll(1, total)
    running_total = 0
    # After we've generated a random number ranging between the totals,
    # keep incrementing the running total by the weight until we hit a number
    # greater than the weight. This should also ignore all possibilities with
    # a probability of 0. 
    for key, weight in choices.iteritems():
        running_total += weight
        if choice_number <= running_total:
            return key


def generate_pclusters():
    ''' Take the definitions of pclusters and create all permutations '''
    global ALL_ONSETS, ALL_CODAS

    ALL_ONSETS = []
    for i in POSSIBLE_ONSETS:
        onsets = i.generate()
        for o in onsets:
            ALL_ONSETS.append(o)

    ALL_CODAS = []
    for i in POSSIBLE_CODAS: 
        codas = i.generate()
        for c in codas:
            ALL_CODAS.append(c)



generate_pclusters()

t = Language()
t.generate_language_properties()

for i in xrange(20):
    t.create_word()


