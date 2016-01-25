
from random import randint as roll
import random

from phonemes import CONSONANTS, VOWELS, POSSIBLE_ONSETS, POSSIBLE_CODAS, EMPTY_CONSONANTS

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

        self.first_onset_no_consonant_chance = roll(20, 80)
        self.final_coda_no_consonant_chance = roll(20, 80)

    def generate_language_properties(self):
        ''' Determine the phonemes which are valid in this language and the 
            frequency at which they occur '''
            
        # Start off by randomly discarding some phonemes that will never be used in this language
        for c in CONSONANTS:
            if roll(1, 100) > 10 and c.num < 300:
                self.valid_consonants.add(c)

        for v in VOWELS:
            if roll(1, 100) > 10: #and v.type != 'diphthong':
                self.valid_vowels.add(v)

        # Now, figure out probabilities for each of the onsets and codas
        # If this language contains all consonants in a possible onset or coda, add a random frequency at which the it occurs
        for o in ALL_ONSETS:
            if all(onset_consonant in self.valid_consonants for onset_consonant in o.consonant_array):
                # Reduce the probability of complex onsets
                if len(o.consonant_array) == 1:     self.onset_probabilities[o] = roll(75, 200)
                elif len(o.consonant_array) > 1:    self.onset_probabilities[o] = roll(1, 5)

        for c in ALL_CODAS:
            if all(coda_consonant in self.valid_consonants for coda_consonant in c.consonant_array):
                # Reduce the probability of complex codas
                if len(c.consonant_array) == 1:     self.coda_probabilities[c] = roll(75, 200)
                elif len(c.consonant_array) > 1:    self.coda_probabilities[c] = roll(1, 5)

        # The placeholder "clusters" for empty onsets/codas
        self.onset_probabilities[EMPTY_CONSONANTS[0]] = int(roll(500, 1000))
        #self.onset_probabilities[EMPTY_CONSONANTS[2]] = int(roll(100, 200))
        self.coda_probabilities[EMPTY_CONSONANTS[1]] = int(roll(450, 900))
        #self.coda_probabilities[EMPTY_CONSONANTS[3]] = int(roll(100, 200))

        # Set vowel probabilities, can vary on preceding and following cluster
        for v in self.valid_vowels:
            # Vowel probabilities are dicts of cluster: probability values,
            # themselves stored by vowel. The overall hashes below look like
            # { {vowel: {cluster: prob}, {cluster: prob}, ...}, {vowel2:{ ... } }  }
            self.vowel_probabilities_by_preceding_cluster[v] = {}
            self.vowel_probabilities_by_following_cluster[v] = {}
            
            diphthong = len(v.position) > 1

            # Choose between low, medium, and high probabilities for this vowel to occur after and before onset and coda clusters
            for (onset, probability) in self.onset_probabilities.iteritems():
                probability = roll(75, 150) if not diphthong else roll(1, 10)
                self.vowel_probabilities_by_preceding_cluster[v][onset] = probability
            
            for (coda, probability) in self.coda_probabilities.iteritems():
                probability = roll(75, 150) if not diphthong else roll(1, 10)
                self.vowel_probabilities_by_following_cluster[v][coda] = probability


    def create_word(self, syllables=2):
        ''' Generate a word in the language, using the appropriate phoneme frequencies '''
        
        word = ''

        previous_coda_complex = 0
        
        for i in xrange(syllables):
            
            ## -------- Handle onset (none if previous coda was complex) ------- ##
            if not previous_coda_complex: onset = weighted_random(self.onset_probabilities)
            else:                         onset = EMPTY_CONSONANTS[0]
            ## ----------------------------------------------------------------- ##

            coda = weighted_random(self.coda_probabilities)
            # Update the flag for whether the previous coda was complex or not
            previous_coda_complex = 1 if len(coda.consonant_array) > 1 else 0

            # Find the probabilities of each vowel occuring based on the phoneme clusters surrounding it
            vowel_probabilities = {v: self.vowel_probabilities_by_preceding_cluster[v][onset] + 
                                      self.vowel_probabilities_by_following_cluster[v][coda] for v in self.valid_vowels}

            vowel = weighted_random(vowel_probabilities)


            word += '{0}{1}{2}'.format(onset.get_string(), vowel.get_string(), coda.get_string())


        
        print word

    def info_dump(self):
        print '\n Onsets \n -', sum(self.onset_probabilities.values())
        onset_probabilities = sorted(((self.onset_probabilities[cons], cons) for cons in self.onset_probabilities.keys()), reverse=True)    
        for perc, c in onset_probabilities:
            print perc, c.get_string()

        print '\n Codas \n -', sum(self.coda_probabilities.values())
        coda_probabilities = sorted(((self.coda_probabilities[cons], cons) for cons in self.coda_probabilities.keys()), reverse=True)    
        for perc, c in coda_probabilities:
            print perc, c.get_string()

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
            # print o.get_string(), o.rule_set

    ALL_CODAS = []
    for i in POSSIBLE_CODAS: 
        codas = i.generate()
        for c in codas:
            ALL_CODAS.append(c)
            # print c.get_string(), c.rule_set

if __name__ == '__main__':
    generate_pclusters()

    t = Language()
    t.generate_language_properties()

    t.info_dump()
    
    for i in xrange(20):
        t.create_word(syllables=roll(1, 2))


