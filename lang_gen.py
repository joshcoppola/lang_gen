
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

        self.valid_vowels = set()
        self.valid_consonants = set()
        
    def generate_language_properties(self):
        ''' Determine the phonemes which are valid in this language and the 
            frequency at which they occur '''
            
        # Start off by randomly discarding some phonemes that will never be used in this language
        for c in CONSONANTS:
            if roll(1, 100) > 10:
                self.valid_consonants.add(c)

        for v in VOWELS:
            if roll(1, 100) > 10 and v.type != 'diphthong':
                self.valid_vowels.add(v)

        # Now, figure out probabilities for each of the onsets and codas
        # If this language contains all consonants in a possible onset or coda, add a random frequency at which the it occurs
        for o in ALL_ONSETS:
            if all(onset_consonant in self.valid_consonants for onset_consonant in o.consonant_array):
                self.onset_probabilities[o] = roll(5, 45)
        
        for c in ALL_CODAS:
            if all(coda_consonant in self.valid_consonants for coda_consonant in c.consonant_array):
                self.coda_probabilities[c] = roll(5, 45)


        # Set vowel probabilities, can vary on preceding and following cluster
        for v in self.valid_vowels:
            # Vowel probabilities are dicts of cluster: probability values,
            # themselves stored by vowel. The overall hashes below look like
            # { {vowel: {cluster: prob}, {cluster: prob}, ...}, {vowel2:{ ... } }  }
            self.vowel_probabilities_by_preceding_cluster[v] = {}
            self.vowel_probabilities_by_following_cluster[v] = {}
            
            # Choose between low, medium, and high probabilities for this vowel to occur after and before onset and coda clusters
            for (onset, probability) in self.onset_probabilities.iteritems():
                self.vowel_probabilities_by_preceding_cluster[v][onset] = random.choice([roll(0, 5), roll(20, 30), roll(50, 75)])
            
            for (coda, probability) in self.coda_probabilities.iteritems():
                self.vowel_probabilities_by_following_cluster[v][coda] = random.choice([roll(0, 5), roll(20, 30), roll(50, 75)]) 


    def create_word(self):
        ''' Generate a word in the language, using the appropriate phoneme frequencies '''
        onset = weighted_random(self.onset_probabilities)
        coda = weighted_random(self.coda_probabilities)
        vowel_probabilities = {}
        
        # Find the probabilities of each vowel occuring based on the phoneme clusters surrounding it
        # TODO - account for empty onsets / codas ... 
        for v in self.valid_vowels:
            onset_weight = self.vowel_probabilities_by_preceding_cluster[v][onset]
            coda_weight = self.vowel_probabilities_by_following_cluster[v][coda]

            vowel_probabilities[v] = onset_weight + coda_weight

        vowel = weighted_random(vowel_probabilities)
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


