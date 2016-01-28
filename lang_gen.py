

import random
from random import randint as roll

import itertools

import phonemes as p
import orthography

# random.seed(100)

''' 
This file generates languages which have distinct phonemes.
'''


LANGUAGE_DROP_VOICING_CHANCE = 5

DROP_COMPLEX_ONSETS_CHANCE = 10
DROP_COMPLEX_CODAS_CHANCE = 10

NO_ONSET_MULTIPLIERS = (.1, .5, 1, 1, 2, 5)
NO_CODA_MULTIPLIERS  = (.1, .25, .5, .5, 1, 2)

ONSET_RESTRICT_VOICING_CHANCE = 20
CODA_RESTRICT_VOICING_CHANCE  = 20

KEEP_VOWEL_CHANCE = 80


def chance(number):
    return roll(1, 100) <= number

class Language:
    def __init__(self):
        self.onset_probabilities = {}
        self.coda_probabilities = {}
        # self.vowel_probabilities_by_preceding_cluster = {}
        # self.vowel_probabilities_by_following_cluster = {}
        self.vowel_flat_probabilities = {}

        self.vocabulary = {}
        self.orthography = orthography.Orthography()

        self.valid_vowels = set(p.VOWELS)
        self.valid_consonants = set([c for c in p.CONSONANTS if c.num < 300])

        self.properties = {}


    def generate_language_properties(self):
        ''' Determine the phonemes which are valid in this language and the 
            frequency at which they occur '''

        for i in xrange( roll(0, 2) ):
            method = random.choice(p.CONSONANT_METHODS)
            print 'Dropping all {0}s'.format(method)
            self.drop_consonants(method=method)

        for i in xrange( roll(0, 2) ):
            location = random.choice(p.CONSONANT_LOCATIONS)
            print 'Dropping all {0}s'.format(location)
            self.drop_consonants(location=location)

        if chance(LANGUAGE_DROP_VOICING_CHANCE):
            voicings = random.choice((0, 1))
            self.properties['language_voicing_restriction'] = voicings
            print 'Dropping with voicing of {0}'.format(voicings)
            self.drop_consonants(voicing=voicings)
        else:
            self.properties['language_voicing_restriction'] = None

        # Some languages have a chance of disallowing complex onsets or complex codas in their syllables
        self.properties['no_complex_onsets'] = 1 if chance(DROP_COMPLEX_ONSETS_CHANCE) else 0
        self.properties['no_complex_codas']  = 1 if chance(DROP_COMPLEX_CODAS_CHANCE) and \
                                                    not self.properties['no_complex_onsets'] else 0
        # Chance of no onset / coda compared to other clusters (a multiplier of 1 means that this onset has a 50% chance
        #  of occuring relative to <any> other onset!
        self.properties['no_onset_multiplier'] = random.choice(NO_ONSET_MULTIPLIERS)
        self.properties['no_coda_multiplier'] =  random.choice(NO_CODA_MULTIPLIERS)

        # ---------- Does the onset have a restriction in voicing? ---------- #
        if chance(ONSET_RESTRICT_VOICING_CHANCE) and self.properties['language_voicing_restriction'] is None:
            self.properties['onset_voicing_restriction']        = roll(0, 1)
            self.properties['invert_onset_voicing_restriction'] = roll(0, 1)
        else:
            self.properties['onset_voicing_restriction']        = None
            self.properties['invert_onset_voicing_restriction'] = None
        # ------------------------------------------------------------------- #

        # ---------- Does the coda have a restriction in voicing? ----------- #
        if chance(CODA_RESTRICT_VOICING_CHANCE) and not self.properties['onset_voicing_restriction'] \
                                                and self.properties['language_voicing_restriction'] is None:
            self.properties['coda_voicing_restriction']        = roll(0, 1)
            self.properties['invert_coda_voicing_restriction'] = roll(0, 1)
        else:
            self.properties['coda_voicing_restriction']        = None
            self.properties['invert_coda_voicing_restriction'] = None
        # ------------------------------------------------------------------- #

        # Now, figure out probabilities for each of the onsets and codas
        # If this language contains all consonants in a possible onset or coda, add a random frequency at which the it occurs
        self.generate_valid_onsets()
        self.generate_valid_codas()


        vowels_to_remove = []
        # Set vowel probabilities, can vary on preceding and following cluster
        for v in self.valid_vowels:
            # # Vowel probabilities are dicts of cluster: probability values,
            # # themselves stored by vowel. The overall hashes below look like
            # # { {vowel: {cluster: prob}, {cluster: prob}, ...}, {vowel2:{ ... } }  }
            # self.vowel_probabilities_by_preceding_cluster[v] = {}
            # self.vowel_probabilities_by_following_cluster[v] = {}

            # # Choose between low, medium, and high probabilities for this vowel to occur after and before onset and coda clusters
            # for (onset, probability) in self.onset_probabilities.iteritems():
            #     # probability = roll(75, 150) if not v.is_diphthong() else roll(1, 8)
            #     probabity = int(random.lognormvariate(3, 1.2))
            #     self.vowel_probabilities_by_preceding_cluster[v][onset] = probability
            
            # for (coda, probability) in self.coda_probabilities.iteritems():
            #     # probability = roll(75, 150) if not v.is_diphthong() else roll(1, 8)
            #     probabity = int(random.lognormvariate(3, 1.2))
            #     self.vowel_probabilities_by_following_cluster[v][coda] = probability
            if chance(KEEP_VOWEL_CHANCE):
                self.vowel_flat_probabilities[v] = int(random.lognormvariate(3, 1.2))
            else:
                vowels_to_remove.append(v)

        # Avoid modifying self.valid_vowels while iterating over it :)
        for vowel in vowels_to_remove:
            self.valid_vowels.remove(vowel)

        ## ------------------------- Print out some info ---------------------------- ##

        self.describe_syllable_level_rules(syllable_part='onset', no_complex=self.properties['no_complex_onsets'],
                                            voicing_restriction=self.properties['onset_voicing_restriction'],
                                            voicing_restriction_exclusion=self.properties['invert_onset_voicing_restriction'])

        self.describe_syllable_level_rules(syllable_part='coda', no_complex=self.properties['no_complex_codas'],
                                            voicing_restriction=self.properties['coda_voicing_restriction'],
                                            voicing_restriction_exclusion=self.properties['invert_coda_voicing_restriction'])

        print 'No onset mutiplier: {0}'.format(self.properties['no_onset_multiplier'])
        print 'No coda mutiplier: {0}'.format(self.properties['no_coda_multiplier'])

        print 'Consonants: {0}; Vowels: {1}\n'.format(len(self.valid_consonants), len(self.valid_vowels))


    def generate_valid_onsets(self):
        ''' Contains some logic for choosing valid onsets for a language, by picking systematic features to disallow '''
        invalid_consonants = self.get_matching_consonants(voicing=self.properties['onset_voicing_restriction'],
                                                          exclude_matches=self.properties['invert_onset_voicing_restriction'])

        for onset in p.ALL_ONSETS:
            # Can't allow the debug empty consonant, or onsets containing invalid consonants
            if onset.is_empty() or not all(onset_consonant in self.valid_consonants for onset_consonant in onset.consonant_array):
                continue

            # No complex onsets if that flag has been set
            elif self.properties['no_complex_onsets'] and onset.is_complex():
                continue

            # If there is a voicing restriction, and the first consonant of the onset matches the restriction, discard the onset
            elif self.properties['onset_voicing_restriction'] is not None and onset.consonant_array[0] in invalid_consonants:
                continue

            # ------ Gauntlet has been run, this onset can now be added to the list ------ #
            elif not onset.is_complex():
                self.onset_probabilities[onset] = int(random.lognormvariate(3, 1.2)) #roll(75, 200)
            # Complex onsets have a much smaller chance of appearing, partially because there's so many of them
            elif onset.is_complex():
                self.onset_probabilities[onset] = int(random.lognormvariate(3, 1.2) / 2) #roll(20, 35)
            # ---------------------------------------------------------------------------- #

        probability_of_no_onset = int(sum(self.onset_probabilities.values()) * self.properties['no_onset_multiplier'])
        self.onset_probabilities[p.EMPTY_CONSONANTS[0]] = probability_of_no_onset


    def generate_valid_codas(self):
        ''' Contains some logic for choosing valid codas for a language, by picking systematic features to disallow '''
        invalid_consonants = self.get_matching_consonants(voicing=self.properties['coda_voicing_restriction'],
                                                          exclude_matches=self.properties['invert_coda_voicing_restriction'])

        for coda in p.ALL_CODAS:
            # Can't allow the debug empty consonant, or codas containing invalid consonants
            if coda.is_empty() or not all(coda_consonant in self.valid_consonants for coda_consonant in coda.consonant_array):
                continue

            # No complex codas if that flag has been set
            elif self.properties['no_complex_codas'] and coda.is_complex():
                continue

            # If there is a voicing restriction, and the last consonant of the coda matches the restriction, discard the coda
            elif self.properties['coda_voicing_restriction'] is not None and coda.consonant_array[-1] in invalid_consonants:
                continue

            # ------ Gauntlet has been run, this coda can now be added to the list ------ #
            elif not coda.is_complex():
                self.coda_probabilities[coda] = int(random.lognormvariate(3, 1.2)) #roll(75, 200)
            # Complex codas have a much smaller chance of appearing, partially because there's so many of them
            elif coda.is_complex():
                self.coda_probabilities[coda] = int(random.lognormvariate(3, 1.2) / 2) #roll(20, 35)
            # ---------------------------------------------------------------------------- #

        probability_of_no_coda = int(sum(self.coda_probabilities.values()) * self.properties['no_coda_multiplier'])
        self.coda_probabilities[p.EMPTY_CONSONANTS[1]] = probability_of_no_coda


    def describe_syllable_level_rules(self, syllable_part, no_complex, voicing_restriction, voicing_restriction_exclusion):
        ''' Placeholder function to describe syllable-level phonemic restrictions '''

        complexity_description = 'cannot be complex' if no_complex else 'can be simple or complex'

        if voicing_restriction is None:
            voicing_description = 'have no voicing restrictions'

        else:
            voicing = 'voiced' if voicing_restriction == 1 else 'unvoiced'

            if voicing_restriction_exclusion == 1:  voicing_description = 'only {0} consonants can appear'.format(voicing)
            else:                                   voicing_description = '{0} consonants cannot appear'.format(voicing)

        print 'Syllable {0}s {1}, and {2}'.format(syllable_part, complexity_description, voicing_description)


    def get_matching_consonants(self, location='any', method='any', voicing='any', exclude_matches=0):
        ''' Given a set of parameters, return an array of consonants that match the parameters '''
        matches = [c for c in self.valid_consonants 
                    if  (location == c.location or location == 'any') 
                    and (method   == c.method   or method   == 'any') 
                    and (voicing  == c.voicing  or voicing  == 'any') ]
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

        self.orthography.phon_to_orth(phoneme_sequence=word)


    def choose_valid_onset(self, previous_coda, syllable_position):
        ''' Business logic for determining whether an onset is valid, given the previous coda and other constraints '''

        # At the beginning of the word, any onset is valid
        if previous_coda is None:
            return weighted_random(self.onset_probabilities)
        # Otherwise, if the previous coda was complex, we'll assign an empty onset
        elif previous_coda.is_complex():
            return p.EMPTY_CONSONANTS[0]
        # No onsets for syllables in the middle of the word if the previous syllable has a coda
        elif syllable_position == 1 and not previous_coda.is_empty():
            return p.EMPTY_CONSONANTS[0]

        # Otherwise, generate an onset with some restrictions
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

            # If the onset has made it through the gauntlet, return it
            return onset


    def choose_valid_coda(self, onset, syllable_position):
        ''' Business logic for determining whether a coda is valid, given the syllable onset and other constraints '''

        # No onsets for syllables in the middle of the word if the previous syllable has a coda
        if syllable_position == 1:
            return p.EMPTY_CONSONANTS[1]

        # Loop through until a valid coda is generated
        while True:
            coda = weighted_random(self.coda_probabilities)
            # No /l/ or /r/ in codas when the onset contains one of these
            if onset.has_any_phoneme( (221, 224) ) and coda.has_any_phoneme( (221, 224) ):
                continue

            # If the coda has made it through the gauntlet, break out of the loop and return it
            return coda


    def choose_valid_vowel(self, onset, coda, syllable_position):
        ''' Choose a valid vowel given an onset, coda, and syllable position '''
        # Find the probabilities of each vowel occuring based on the phoneme clusters surrounding it
        # vowel_probabilities = {v: self.vowel_probabilities_by_preceding_cluster[v][onset] + 
        #                           self.vowel_probabilities_by_following_cluster[v][coda] for v in self.valid_vowels}                         
        
        while True:
            # Generate the vowel based off of the combined weighings of the vowels surrounding it
            # vowel = weighted_random(vowel_probabilities)
            vowel = weighted_random(self.vowel_flat_probabilities)

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
        if total_syllables == 1:    return -1
        # On the first syllable
        if current_syllable == 0:   return 0
        # On the last syllable
        elif current_syllable == \
             total_syllables - 1:   return 2
        # Otherwise, it's in the middle
        else:                       return 1


    def info_dump(self):
        table_data = []

        onset_probabilities = sorted(((self.onset_probabilities[cons], cons) for cons in self.onset_probabilities.keys()), reverse=True)
        table_data.append(['{0: >4} {1}'.format(perc, c.get_string()) for perc, c in onset_probabilities])

        coda_probabilities = sorted(((self.coda_probabilities[cons], cons) for cons in self.coda_probabilities.keys()), reverse=True)
        table_data.append(['{0: >4} {1}'.format(perc, c.get_string()) for perc, c in coda_probabilities])

        vowel_probabilities = sorted(((self.vowel_flat_probabilities[v], v) for v in self.vowel_flat_probabilities.keys()), reverse=True)
        table_data.append(['{0: >4} {1}'.format(perc, v.get_string()) for perc, v in vowel_probabilities])


        print("{: <12} {: <12} {: <12}".format('Onsets', 'Codas', 'Vowels'))
        for row in itertools.izip_longest(*table_data, fillvalue=""):
            print("{: <12} {: <12} {: <12}".format(*row))

        print ''


def weighted_random(choices):
    ''' Naive algorithm. Input a dict of possibility: weight, 
    where weight must be an integer for this to function 100% 
    correctly. Returns the choice '''
    total = sum(choices.values())

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


if __name__ == '__main__':
    print ''

    t = Language()
    t.generate_language_properties()

    t.info_dump()
    
    # print ' ---->', roll(1, 100), '<----'
    for i in xrange(20):
        t.create_word(syllables=random.choice( (1, 1, 1, 1, 2, 2, 3) ))
    # print ' ---->', roll(1, 100), '<----'
    print ''

