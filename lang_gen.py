
from random import randint as roll
import random

from phonemes import CONSONANTS, VOWELS, POSSIBLE_ONSETS, POSSIBLE_CODAS, EMPTY_CONSONANTS, CONSONANT_METHODS, CONSONANT_LOCATIONS

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

        self.valid_vowels = set(VOWELS)
        self.valid_consonants = set([c for c in CONSONANTS if c.num < 300])

    def generate_language_properties(self):
        ''' Determine the phonemes which are valid in this language and the 
            frequency at which they occur '''

        # Prob of methods:  plosive, affricate, fricative, nasal, approximant, lateral
        #  -- Some langs may drop any of these entirely
        # Prob of locations: bilabial, alveolar, velar, post-alveolar, labio-dental, dental, glottal, palatal
        #  -- Some langs may drop any of these entirely
        # Voicings: voiced, unvoiced
        #  -- Some langs may force only voiced or unvoiced consonants
        #       -- Specific rules on an onset or coda level? (only voiced consonants in onset / coda, etc)
        # Prob of no onset / coda

        voicings = (0, 1)

        for i in xrange( roll(0, 2) ):
            method = random.choice(CONSONANT_METHODS)
            print 'Dropping all {0}s'.format(method)
            self.drop_consonants(method=method)

        for i in xrange( roll(0, 2) ):
            location = random.choice(CONSONANT_LOCATIONS)
            print 'Dropping all {0}s'.format(location)
            self.drop_consonants(location=location)

        if roll(1, 5) == 1:
            voicings = random.choice(voicings)
            print 'Dropping with voicing of {0}'.format(voicings)
            self.drop_consonants(voicing=voicings)

        # Now, figure out probabilities for each of the onsets and codas
        # If this language contains all consonants in a possible onset or coda, add a random frequency at which the it occurs
        no_complex_onsets, onset_voicing_restriction = self.generate_valid_onsets()
        no_complex_codas, coda_voicing_restriction = self.generate_valid_codas(no_complex_onsets=no_complex_onsets, onset_voicing_restriction=onset_voicing_restriction)

        print 'Complex onsets: {0}\nOnset voicing restriction: {1}'.format(not no_complex_onsets, onset_voicing_restriction)
        print 'Complex codas:  {0}\nCoda voicing restriction: {1}'.format(not no_complex_codas,  coda_voicing_restriction)

        # Chance of no onset compared to other syllables
        no_onset_multiplier = random.choice( (.1, .5, 1, 1, 2, 10) )
        no_coda_multiplier =  random.choice( (.1, .25, .5, .5, 1, 2) )
        print 'No onset mutiplier: {0}\nNo coda multiplier: {1}\n'.format(no_onset_multiplier, no_coda_multiplier)

        # The placeholder "clusters" for empty onsets/codas
        self.onset_probabilities[EMPTY_CONSONANTS[0]] = int(sum(self.onset_probabilities.values()) * no_onset_multiplier)
        self.coda_probabilities[EMPTY_CONSONANTS[1]] =  int(sum(self.coda_probabilities.values())  * no_coda_multiplier) 

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

        print 'Consonants: {0}; Vowels: {1}\n'.format(len(self.valid_consonants), len(self.valid_vowels))

    def generate_valid_onsets(self):
        ''' Contains some logic for choosing valid onsets for a language, by picking systematic features to disallow '''
        no_complex_onsets = 1 if roll(1, 10) == 10 else 0

        onset_voicing_restriction = roll(0, 1) if roll(1, 5) == 1 else None

        consonants_matching_voicing_restriction = []
        if onset_voicing_restriction is not None:
            voicing_restriction_exclusion = roll(0, 1)
            consonants_matching_voicing_restriction = self.get_matching_consonants(voicing=onset_voicing_restriction, exclude_matches=voicing_restriction_exclusion)

        for onset in ALL_ONSETS:
            # Can't allow the debug empty consonant, or onsets containing invalid consonants
            if onset.is_empty() or not all(onset_consonant in self.valid_consonants for onset_consonant in onset.consonant_array):
                continue

            # No complex onsets if that flag has been set
            elif no_complex_onsets and onset.is_complex():
                continue

            # If there is a voicing restriction, and the first consonant of the onset matches the restriction, discard the onset
            elif onset_voicing_restriction is not None and onset.consonant_array[0] in consonants_matching_voicing_restriction:
                continue


            # ------ Gauntlet has been run, this onset can now be added to the list ------ #
            elif not onset.is_complex():
                self.onset_probabilities[onset] = roll(75, 200)
            # Complex onsets have a much smaller chance of appearing, partially because there's so many of them
            elif onset.is_complex():
                self.onset_probabilities[onset] = roll(5, 15)
            # ---------------------------------------------------------------------------- #

        return no_complex_onsets, onset_voicing_restriction


    def generate_valid_codas(self, no_complex_onsets, onset_voicing_restriction):
        ''' Contains some logic for choosing valid codas for a language, by picking systematic features to disallow '''
        no_complex_codas = 1 if (roll(1, 10) == 10 and not no_complex_onsets) else 0

        coda_voicing_restriction = roll(0, 1) if (roll(1, 5) == 1 and onset_voicing_restriction is None) else None

        consonants_matching_voicing_restriction = []
        if coda_voicing_restriction is not None:
            voicing_restriction_exclusion = roll(0, 1)
            consonants_matching_voicing_restriction = self.get_matching_consonants(voicing=coda_voicing_restriction, exclude_matches=voicing_restriction_exclusion)

        for coda in ALL_CODAS:
            # Can't allow the debug empty consonant, or codas containing invalid consonants
            if coda.is_empty() or not all(coda_consonant in self.valid_consonants for coda_consonant in coda.consonant_array):
                continue

            # No complex codas if that flag has been set
            elif no_complex_codas and coda.is_complex():
                continue

            # If there is a voicing restriction, and the first consonant of the coda matches the restriction, discard the coda
            elif coda_voicing_restriction is not None and coda.consonant_array[0] in consonants_matching_voicing_restriction:
                continue


            # ------ Gauntlet has been run, this coda can now be added to the list ------ #
            elif not coda.is_complex():
                self.coda_probabilities[coda] = roll(75, 200)
            # Complex codas have a much smaller chance of appearing, partially because there's so many of them
            elif coda.is_complex():
                self.coda_probabilities[coda] = roll(5, 15)
            # ---------------------------------------------------------------------------- #

        return no_complex_codas, coda_voicing_restriction



    def get_matching_consonants(self, location='any', method='any', voicing='any', exclude_matches=0):
        ''' Given a set of parameters, return an array of consonants that match the parameters '''
        matches = [c for c in self.valid_consonants 
                    if  (location == c.location or location == 'any') 
                    and (method   == c.method   or method   == 'any') 
                    and (voicing  == c.voicing  or voicing  == 'any') 
                    ]

        # exclude_matches as basically "not" - if that option is toggled on, build a new list of all 
        # results which didn't match the query. 
        if not exclude_matches: query_result = matches  
        else:                   query_result = [c for c in self.valid_consonants if c not in matches]

        return query_result

    def drop_consonants(self, location='any', method='any', voicing='any'):
        ''' Remove a set of consonants matching certain parameters from this language ''' 
        for consonant in self.get_matching_consonants(location=location, method=method, voicing=voicing):
            self.valid_consonants.remove(consonant)


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

