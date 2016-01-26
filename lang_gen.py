
from random import randint as roll
import random

from phonemes import CONSONANTS, VOWELS, POSSIBLE_ONSETS, POSSIBLE_CODAS, EMPTY_CONSONANTS

import orthography


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
        self.orthography = orthography.Orthography()

        self.valid_vowels = set()
        self.valid_consonants = set()

    def generate_language_properties(self):
        ''' Determine the phonemes which are valid in this language and the 
            frequency at which they occur '''
            
        # Start off by randomly discarding some phonemes that will never be used in this language
        for c in CONSONANTS:
            if roll(1, 100) > 15 and c.num < 300:
                self.valid_consonants.add(c)

        for v in VOWELS:
            if roll(1, 100) > 15: #and v.type != 'diphthong':
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
        self.coda_probabilities[EMPTY_CONSONANTS[1]] = int(roll(450, 900))

        # Set vowel probabilities, can vary on preceding and following cluster
        for v in self.valid_vowels:
            # Vowel probabilities are dicts of cluster: probability values,
            # themselves stored by vowel. The overall hashes below look like
            # { {vowel: {cluster: prob}, {cluster: prob}, ...}, {vowel2:{ ... } }  }
            self.vowel_probabilities_by_preceding_cluster[v] = {}
            self.vowel_probabilities_by_following_cluster[v] = {}

            # Choose between low, medium, and high probabilities for this vowel to occur after and before onset and coda clusters
            for (onset, probability) in self.onset_probabilities.iteritems():
                probability = roll(75, 150) if not v.is_diphthong() else roll(1, 8)
                self.vowel_probabilities_by_preceding_cluster[v][onset] = probability
            
            for (coda, probability) in self.coda_probabilities.iteritems():
                probability = roll(75, 150) if not v.is_diphthong() else roll(1, 8)
                self.vowel_probabilities_by_following_cluster[v][coda] = probability


    def create_word(self, syllables=2):
        ''' Generate a word in the language, using the appropriate phoneme frequencies '''
        
        word = []
        # Set to None so that the first onset knows that it's word-initial (no coda comes before the first syllable)
        coda = None

        for i in xrange(syllables):            
            syllable_position = self.get_syllable_position(current_syllable=i, total_syllables=syllables)

            onset = self.choose_valid_onset(previous_coda=coda, syllable_position=syllable_position)
            coda  = self.choose_valid_coda(onset=onset, syllable_position=syllable_position)

            vowel = self.choose_valid_vowel(onset=onset, coda=coda, syllable_position=syllable_position)

            word.extend([c.num for c in onset.consonant_array])
            word.append(vowel.num)
            word.extend([c.num for c in coda.consonant_array])
            # word += '{0}{1}{2}'.format(onset.get_string(), vowel.get_string(), coda.get_string())

        self.orthography.phon_to_orth(phoneme_sequence=word)
        # print ''.join([orthography.PHONEMES_WRITTEN[phoneme] for phoneme in word])


    def choose_valid_onset(self, previous_coda, syllable_position):
        ''' Business logic for determining whether an onset is valid, given the previous coda and other constraints '''

        # At the beginning of the word, any onset is valid
        if previous_coda is None:
            onset = weighted_random(self.onset_probabilities)

        # Otherwise, if the previous coda was complex, we'll assign an empty onset
        elif previous_coda.is_complex():
            onset = EMPTY_CONSONANTS[0]

        # No onsets for syllables in the middle of the word if the previous syllable has a coda
        elif syllable_position == 1 and not previous_coda.is_empty():
            onset = EMPTY_CONSONANTS[0]

        # Otherwise, generate an onset with some restrictions
        else:
            # Stash the previous coda's last phoneme in case we need to check it multiple times
            previous_coda_last_phoneme = previous_coda.consonant_number_array[-1]

            # Loop through and generate onsets until one matches all criteria
            while True:
                onset = weighted_random(self.onset_probabilities)

                # Can't start one syllable off with the same phoneme that the previous ended with
                if onset.consonant_number_array[-1] == previous_coda_last_phoneme:
                    continue

                # Can't have an open coda followed by an empty onset
                if onset.is_empty() and previous_coda.is_empty():
                    continue

                break

        return onset

    def choose_valid_coda(self, onset, syllable_position):
        ''' Business logic for determining whether a coda is valid, given the syllable onset and other constraints '''

        # No onsets for syllables in the middle of the word if the previous syllable has a coda
        if syllable_position == 1:
            coda = EMPTY_CONSONANTS[1]

        else:
            # No /l/ or /r/ in codas when the onset contains one of these 
            restrict_rl = onset.has_any_phoneme( (221, 224) )

            while True:
                coda = weighted_random(self.coda_probabilities)

                # No /l/ or /r/ in codas when the onset contains one of these 
                if restrict_rl and coda.has_any_phoneme( (221, 224)):
                    continue

                # If the coda has made it through the gauntlet, break out of the loop and return it
                break

        return coda


    def choose_valid_vowel(self, onset, coda, syllable_position):
        ''' Choose a valid vowel given an onset, coda, and syllable position '''

        # Find the probabilities of each vowel occuring based on the phoneme clusters surrounding it
        vowel_probabilities = {v: self.vowel_probabilities_by_preceding_cluster[v][onset] + 
                                  self.vowel_probabilities_by_following_cluster[v][coda] for v in self.valid_vowels}
        
        while True:
            # Generate the vowel based off of the combined weighings of the vowels surrounding it
            vowel = weighted_random(vowel_probabilities)

            # A short vowel cannot occur if there is no consonant in the coda
            if coda.is_empty() and vowel.length == 'short':
                continue

            # Only short vowels can occur before /ng/
            if coda.consonant_number_array[0] == 220 and vowel.length != 'short':
                continue

            # If the vowel has made it through the gauntlet, break out of the loop and return it
            break


        return vowel



    def get_syllable_position(self, current_syllable, total_syllables):
        ''' Get the position of a syllable within a word
            - 1 = only 1 syllable in the word
            0   = word initial
            1   = middle
            2   = final
        '''

        # Only 1 syllable in the word
        if total_syllables == 1:
            return -1
        # On the first syllable
        if current_syllable == 0:
            return 0
        # On the last syllable
        elif current_syllable == total_syllables - 1:
            return 2
        # Otherwise, it's in the middle
        else:
            return 1


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
    print ''
    generate_pclusters()

    t = Language()
    t.generate_language_properties()

    # t.info_dump()
    
    for i in xrange(20):
        t.create_word(syllables=roll(1, 3))

    print ''

