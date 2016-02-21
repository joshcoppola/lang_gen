
from __future__ import division, unicode_literals
import random
from random import randint as roll
from collections import namedtuple, OrderedDict

import itertools

import phonemes as p
import orthography


''' 
This file generates languages which have distinct phonemes.
'''

# Chance of dropping an entire articulation method from the language
DROP_ENTIRE_METHOD_CHANCE = 5
# Chance of dropping an entire articulation location from the language
DROP_ENTIRE_LOCATION_CHANCE = 10
# Chance of dropping "th" from the language
DROP_DENTAL_CHANCE = 65
# Chance of dropping an entire voicing method (voiced / unvoiced) from the language
DROP_ENTIRE_VOICING_CHANCE = 5

# Won't drop random consonants if fewer than this many consonants exist after the above
DROP_RANDOM_CONSONANT_THRESHHOLD = 15
# Chance of dropping random consonant
DROP_RANDOM_CONSONANT_CHANCE = 80
# If dropping a random consonant it triggered, how many to drop?
DROP_RANDOM_CONSONANT_AMOUNTS = (1, 1, 1, 1, 2, 2, 2, 3)

# SYLLABLE_STRUCTURE_CHANCES = {
#     'no codas': 40,
#     'no onsets': 20,
#     'onsets and codas': 60
# }

# What types of plosive can exist in the language
PLOSIVE_TYPES = {
    'unaspirated': 50,
    'aspirated': 35,
    'aspirated and unaspirated': 25
}

# Chance of dropping all non-english phonemes
FORCE_ENGLISH_PHONEMES_CHANCE = 25
# If language has not forced english phonemes only, it will pick one of 
# these percentages of non-english phonemes to drop 
DROP_NON_ENGLISH_PHONEME_CHANCES = (25, 50, 75, 90, 90)


# The chance that a particular language will forbid complex onsets
DROP_COMPLEX_ONSETS_CHANCE = 35
# The chance that a particular language will forbid complex codas 
DROP_COMPLEX_CODAS_CHANCE = 35

# This is the proportion of null onsets or codas that a language has in relation 
# to all other onsets. A multiplier of 1 means null onsets occur 50% of the time
# and a multiplier of .1 means null onsets occur 10% of the time
NO_ONSET_MULTIPLIERS = (.25, .5, 1, 1, 2, 5)
NO_CODA_MULTIPLIERS  = (.25, .5, .5, 1, 2)

# The chances of having a language restrict syllable onsets or codas by voicing
ONSET_RESTRICT_VOICING_CHANCE = 15
CODA_RESTRICT_VOICING_CHANCE  = 15

# The chance of dropping all diphthongs or dropping all lax monphthong vowels
DROP_ALL_DIPHTHONGS_CHANCE = 25
DROP_ALL_LAX_MONPHTHONGS_CHANCE = 20
# The chance of dropping all rounded vowels
DROP_ALL_ROUNDED_CHANCE = 10
# The chance of dropping random monophthongs / diphthongs
DROP_RANDOM_MONOPHTHONG_CHANCE = 20
DROP_RANDOM_DIPHTHONG_CHANCE   = 40

MIN_NUM_VOWELS = 4

# -- For complex syllable components, their probability is reduced by these amounts -- #
COMPLEX_ONSET_PROBABILITY_MULTIPLIER = .35

COMPLEX_CODA_PROBABILITY_MULTIPLIER = .35

DIPHTHONG_PROBABILITY_MULTIPLIER = .35

# This is the probability that an empty onset will be forced after a syllable with any coda
# Otherwise, certain languages may have high probabilities of big multi-consonant clusters
# which are valid but hard to read (especially in 3+ syllable words)
FORCE_EMPTY_ONSET_AFTER_ANY_CODA_CHANCE = 35


def chance(number, top=100):
    ''' A simple function for automating a chance (out of 100) of something happening '''
    return roll(1, top) <= number

# A data structure containing phoneme #s for different parts of the syllable
Syllable = namedtuple('Syllable', ['onset', 'nucleus', 'coda'])

class Word:
    def __init__(self, syllables):
        self.syllables = syllables

        # Writing as a generator comprehension for speed, at the cost of readability?
        self.phoneme_ids =  tuple(phoneme_id 
                            for syllable in syllables
                                for component in syllable
                                    for phoneme_id in component)

    def __len__(self):
        return len(self.phoneme_ids)

    def get_phonemes(self):
        ''' A generator which returns the phoneme id and position within the syllable
            for all phonemes in the word, in addition to the syllable component and whether
            or not this particular position is at a boundary between syllables '''
        phoneme_index = -1

        for syllable_number, syllable in enumerate(self.syllables):
            # Each component in the syllable has one or more phoneme ids
            for component_index, phoneme_ids in enumerate(syllable):
                # A syllable component can have more than one phoneme (/spr/, /rt/, etc)
                for phoneme_position_within_component, phoneme_id in enumerate(phoneme_ids):
                    phoneme_index += 1
                    
                    position_info = self.get_phoneme_position_info(phoneme_index=phoneme_index)
                    # If this isn't the first syllable, and is an onset (component index == 0) 
                    # and it's the first phoneme in the onset  -- it's a boundary between syllables
                    position_info['is_boundary_between_syllables'] = \
                        (syllable_number > 0 and component_index == 0 and phoneme_position_within_component == 0)


                    yield phoneme_id, position_info


    def get_phoneme_position_info(self, phoneme_index):
        ''' Get information regarding this phoneme's position in the word '''
        at_beginning = phoneme_index == 0
        at_end       = phoneme_index == len(self) - 1

        phoneme_position_info = {
            'before_consonant': not at_end       and p.data.is_consonant(self.phoneme_ids[phoneme_index + 1]),
            'after_consonant':  not at_beginning and p.data.is_consonant(self.phoneme_ids[phoneme_index - 1]), 
            'at_beginning':     at_beginning, 
            'at_end':           at_end,
        }

        return phoneme_position_info


class Language:
    def __init__(self):
        self.properties = {}

        self.valid_consonants = {c for c in p.CONSONANTS if c.id_ < 300}
        self.probabilities = { 'onset': {}, 'coda':{}, 'nucleus':{} }
        
        # Will be created at end of nucleus step - this will be used as a quick way to
        # generate monophthongs rather then potentially getting dipthongs later
        self.nuclei_with_monophthong_probabilities = {}

        self.vocabulary = {}
        self.orthography = None

        # Log some of the rules that get flagged for this language
        self.log = []

    def generate_language_properties(self):
        ''' Determine the phonemes which are valid in this language and the 
            frequency at which they occur '''
        
        # ------------------------- Drop some phonemes at the language level ----------------------- #
        if chance(DROP_ENTIRE_METHOD_CHANCE):
            method = random.choice(p.data.consonant_methods)
            self.log.append('Dropping all {0}s'.format(method))
            self.drop_consonants(method=method)

        if chance(DROP_DENTAL_CHANCE):
            self.log.append('Dropping dentals')
            self.drop_consonants(location='dental')

        if chance(DROP_ENTIRE_LOCATION_CHANCE):
            location = random.choice(p.data.consonant_locations)
            self.log.append('Dropping all {0}s'.format(location))
            self.drop_consonants(location=location)

        if chance(DROP_ENTIRE_VOICING_CHANCE):
            voicings = random.choice((0, 1))
            self.properties['language_voicing_restriction'] = voicings
            self.log.append('Dropping with voicing of {0}'.format(voicings))
            self.drop_consonants(voicing=voicings)
        else:
            self.properties['language_voicing_restriction'] = None


        # Figure out if this language distinguishes between aspirated / unaspirated plosives
        plosive_types = weighted_random(PLOSIVE_TYPES)
        if      plosive_types == 'unaspirated': self.drop_consonants(method='plosive', special='aspirated')
        elif    plosive_types == 'aspirated':   self.drop_consonants(method='plosive', special=None)
        elif    plosive_types == 'aspirated and unaspirated': pass
        self.properties['plosive_types'] = plosive_types
        self.log.append('Allow {0} plosives'.format(plosive_types))

        
        # ------------------- Figure out which non-english phonemes to drop ------------------- #

        self.properties['non_english_phoneme_chances'] = None
        non_english_phonemes = [c for c in self.valid_consonants if not c.is_english()]

        # Chance of forcing only english phonemes (so, drop all non-english ones)
        if chance(FORCE_ENGLISH_PHONEMES_CHANCE):
            self.properties['non_english_phoneme_chances'] = 0
            self.log.append("All phonemes must be English")
            # Actually drop the phonemes
            for c in non_english_phonemes:
                self.valid_consonants.remove(c)

        # Otherwise, a language gets a random rate of dropping a non-english phoneme,
        # and then will go through and drop non-english phonemes at that rate
        else:
            drop_non_english_phoneme_chance = random.choice(DROP_NON_ENGLISH_PHONEME_CHANCES)
            self.properties['non_english_phoneme_chances'] = 100 - drop_non_english_phoneme_chance
            self.log.append("{0}% chance of dropping non-english phonemes".format(drop_non_english_phoneme_chance))
            # Actually drop the phonemes
            for c in non_english_phonemes:
                if chance(drop_non_english_phoneme_chance):
                    self.valid_consonants.remove(c)

        # ------------------------------------------------------------------------------------- #


        # There is a chance for one or more random consonants to be removed as well
        if len(self.valid_consonants) >= DROP_RANDOM_CONSONANT_THRESHHOLD and \
                                            chance(DROP_RANDOM_CONSONANT_CHANCE):

            for i in xrange(random.choice(DROP_RANDOM_CONSONANT_AMOUNTS)):
                random_consonant = random.choice(tuple(self.valid_consonants))
                self.valid_consonants.remove(random_consonant)

        # Finally, choose some valid nuclei (vowels) in this language
        self.generate_valid_nuclei()
        # ---------------------------- End language-level phoneme rules ------------------------------- #


        # Some languages have a chance of disallowing complex onsets or complex codas in their syllables
        self.properties['no_complex_onsets'] = 1 if chance(DROP_COMPLEX_ONSETS_CHANCE) else 0
        self.properties['no_complex_codas']  = 1 if chance(DROP_COMPLEX_CODAS_CHANCE)  else 0
        # Chance of no onset / coda compared to other clusters (a multiplier of 1 means that this onset has a 50% chance
        #  of occuring relative to <any> other onset!
        self.properties['no_onset_multiplier'] = random.choice(NO_ONSET_MULTIPLIERS)
        self.properties['no_coda_multiplier']  = random.choice(NO_CODA_MULTIPLIERS)

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
        self.generate_valid_onsets()
        self.generate_valid_codas()


        ## ------------------------- Print out some info ---------------------------- ##

        self.log.append( self.describe_syllable_level_rules(syllable_part='onset', no_complex=self.properties['no_complex_onsets'],
                                            voicing_restriction=self.properties['onset_voicing_restriction'],
                                            voicing_restriction_exclusion=self.properties['invert_onset_voicing_restriction']) )

        self.log.append( self.describe_syllable_level_rules(syllable_part='coda', no_complex=self.properties['no_complex_codas'],
                                            voicing_restriction=self.properties['coda_voicing_restriction'],
                                            voicing_restriction_exclusion=self.properties['invert_coda_voicing_restriction']) )

        self.log.append( 'No onset mutiplier: {0}'.format(self.properties['no_onset_multiplier']) )
        self.log.append( 'No coda mutiplier: {0}'.format(self.properties['no_coda_multiplier']) )

        self.log.append( 'Consonants: {0}; Vowels: {1}\n'.format(len(self.valid_consonants), len(self.probabilities['nucleus'])) )


        ## -------------------------- Set orthography -------------------------------- ##

        self.orthography = orthography.Orthography(parent_language=self)


    def generate_valid_onsets(self):
        ''' Contains some logic for choosing valid onsets for a language, by picking systematic features to disallow '''
        invalid_consonants = self.get_matching_consonants(voicing=self.properties['onset_voicing_restriction'],
                                                          exclude_matches=self.properties['invert_onset_voicing_restriction'])

        for onset in p.data.syllable_onsets:
            # Can't allow the debug empty consonant, or onsets containing invalid consonants
            if onset.is_empty() or not all(onset_consonant in self.valid_consonants for onset_consonant in onset.phonemes):
                continue

            # No complex onsets if that flag has been set
            elif self.properties['no_complex_onsets'] and onset.is_complex():
                continue

            # If there is a voicing restriction, and the first consonant of the onset matches the restriction, discard the onset
            elif self.properties['onset_voicing_restriction'] is not None and onset.phonemes[0] in invalid_consonants:
                continue

            # ------ Gauntlet has been run, this onset can now be added to the list ------ #
            self.probabilities['onset'][onset] = self.get_component_probability(component_type='onset', component=onset)
            

        probability_of_no_onset = int(sum(self.probabilities['onset'].values()) * self.properties['no_onset_multiplier'])
        self.probabilities['onset'][p.data.empty_onset] = probability_of_no_onset


    def generate_valid_codas(self):
        ''' Contains some logic for choosing valid codas for a language, by picking systematic features to disallow '''
        invalid_consonants = self.get_matching_consonants(voicing=self.properties['coda_voicing_restriction'],
                                                          exclude_matches=self.properties['invert_coda_voicing_restriction'])

        for coda in p.data.syllable_codas:
            # Can't allow the debug empty consonant, or codas containing invalid consonants
            if coda.is_empty() or not all(coda_consonant in self.valid_consonants for coda_consonant in coda.phonemes):
                continue

            # No complex codas if that flag has been set
            elif self.properties['no_complex_codas'] and coda.is_complex():
                continue

            # If there is a voicing restriction, and the last consonant of the coda matches the restriction, discard the coda
            elif self.properties['coda_voicing_restriction'] is not None and coda.phonemes[-1] in invalid_consonants:
                continue

            # ------ Gauntlet has been run, this coda can now be added to the list ------ #
            self.probabilities['coda'][coda] = self.get_component_probability(component_type='coda', component=coda)


        probability_of_no_coda = int(sum(self.probabilities['coda'].values()) * self.properties['no_coda_multiplier'])
        self.probabilities['coda'][p.data.empty_coda] = probability_of_no_coda


    def generate_valid_nuclei(self):
        ''' Contains some logic for choosing which vowels will be used in this language '''

        # -------- Set some initial parameters -------- #
        drop_all_diphtongs = chance(DROP_ALL_DIPHTHONGS_CHANCE)

        if drop_all_diphtongs:  drop_all_lax_monophthongs = chance(DROP_ALL_LAX_MONPHTHONGS_CHANCE)
        else:                   drop_all_lax_monophthongs = 0

        if not drop_all_diphtongs and \
           not drop_all_lax_monophthongs: drop_all_rounded = chance(DROP_ALL_ROUNDED_CHANCE)
        else:                             drop_all_rounded = 0
        # ------- End setting initial parameters ------- #

        # Set vowel probabilities, can vary on preceding and following cluster
        for nucleus in p.data.syllable_nuclei:
            # Nuclei will always have 1 phoneme - the vowel
            vowel = nucleus.phonemes[0]

            if drop_all_diphtongs and vowel.is_diphthong():
                continue
            if drop_all_lax_monophthongs and vowel.manner == 'lax':
                continue
            if drop_all_rounded and vowel.lips == 'rounded':
                continue

            # Drop random vowels
            if not vowel.is_diphthong() and chance(DROP_RANDOM_MONOPHTHONG_CHANCE):
                continue
            if vowel.is_diphthong() and chance(DROP_RANDOM_DIPHTHONG_CHANCE):
                continue

            self.probabilities['nucleus'][nucleus] = self.get_component_probability(component_type='nucleus', component=nucleus)

        # -------- Cleanup - ensure a language has at least MIN_NUM_VOWELS vowels ------------ #

        # If somehow we've ended up with a ridiculously low number of vowels,
        # this loop ensures we'll be brought up to above 5 vowels total
        while len(self.probabilities['nucleus']) < MIN_NUM_VOWELS:
            random_new_nucleus = random.choice(tuple(p.data.syllable_nuclei))
            if random_new_nucleus not in self.probabilities['nucleus']:
                self.probabilities['nucleus'][random_new_nucleus] = \
                                        self.get_component_probability(component_type='nucleus', component=random_new_nucleus)

        
        # -------- Cleanup - ensure a diphthong does not occur as the most probable vowel type ------------ #

        sorted_nuclei_probabilities = sorted([(self.probabilities['nucleus'][nucleus], nucleus) 
                                            for nucleus in self.probabilities['nucleus']], reverse=True)

        most_probable_vowel_nucleus = sorted_nuclei_probabilities[0][1]
        # Find the first monophthong, which will be used to swap with the most probable vowel 
        _, most_probable_monophthong_nucleus = \
            next((probability, nucleus) for probability, nucleus in sorted_nuclei_probabilities 
                                            if not nucleus.phonemes[0].is_diphthong())
        # for probability, nucleus in sorted_nuclei_probabilities:
        #     vowel = nucleus.phonemes[0]
        #     if not vowel.is_diphthong():
        #         most_probable_monophthong_nucleus = nucleus
        #         break

        if most_probable_vowel_nucleus != most_probable_monophthong_nucleus:
            self.log.append( "Flipping {0} with {1}".format(most_probable_vowel_nucleus.get_string(), most_probable_monophthong_nucleus.get_string()) )
            # Flip the probabilities
            self.probabilities['nucleus'][most_probable_monophthong_nucleus], self.probabilities['nucleus'][most_probable_vowel_nucleus] = \
                self.probabilities['nucleus'][most_probable_vowel_nucleus], self.probabilities['nucleus'][most_probable_monophthong_nucleus]

        # ----------- Cleanup - Build a list of just nuclei with monophthongs for later use  --------------- #

        self.nuclei_with_monophthong_probabilities = {nucleus: self.probabilities['nucleus'][nucleus] 
                                                        for nucleus in self.probabilities['nucleus'] 
                                                            if not nucleus.phonemes[0].is_diphthong() }

        # ---------------------------------------- End Cleanup --------------------------------------------- #


    def get_component_probability(self, component_type, component):
        ''' Once a syllable component (onset, coda, or nucleus) has been generated and needs to be 
            added to the language, this method handles generating the probability and adding it '''

        # ------------------------------ Onset ------------------------------ #
        if component_type == 'onset':
            if not component.is_complex():  return int(random.lognormvariate(3, 1.2)) 
            elif   component.is_complex():  return int(random.lognormvariate(3, 1.2) * COMPLEX_ONSET_PROBABILITY_MULTIPLIER)

        # ------------------------------ Coda ------------------------------- #
        elif component_type == 'coda':
            if not component.is_complex():  return int(random.lognormvariate(3, 1.2))
            elif   component.is_complex():  return int(random.lognormvariate(3, 1.2) * COMPLEX_CODA_PROBABILITY_MULTIPLIER)

        # ------------------------------ Nucleus ----------------------------- #
        elif component_type == 'nucleus':
            vowel = component.phonemes[0]
            
            if not vowel.is_diphthong():    return int(random.lognormvariate(3, 1.2))
            else:                           return int(random.lognormvariate(3, 1.2) * DIPHTHONG_PROBABILITY_MULTIPLIER)


    def describe_syllable_level_rules(self, syllable_part, no_complex, voicing_restriction, voicing_restriction_exclusion):
        ''' Placeholder function to describe syllable-level phonemic restrictions '''

        complexity_description = 'cannot be complex' if no_complex else 'can be simple or complex'

        if voicing_restriction is None:
            voicing_description = 'have no voicing restrictions'

        else:
            voicing = 'voiced' if voicing_restriction == 1 else 'unvoiced'

            if voicing_restriction_exclusion == 1:  voicing_description = 'only {0} consonants can appear'.format(voicing)
            else:                                   voicing_description = '{0} consonants cannot appear'.format(voicing)

        return 'Syllable {0}s {1}, and {2}'.format(syllable_part, complexity_description, voicing_description)


    def get_matching_consonants(self, location='any', method='any', voicing='any', special='any', exclude_matches=0):
        ''' Given a set of parameters, return an array of consonants that match the parameters '''
        matches = [c for c in self.valid_consonants 
                    if  (location == c.location or location == 'any') 
                    and (method   == c.method   or method   == 'any') 
                    and (voicing  == c.voicing  or voicing  == 'any')
                    and (special  == c.special  or special  == 'any') ]
        # exclude_matches as basically "not" - if that option is toggled on, build a new list of all 
        # results which didn't match the query. 
        if not exclude_matches: query_result = matches  
        else:                   query_result = [c for c in self.valid_consonants if c not in matches]

        return query_result

    def drop_consonants(self, location='any', method='any', voicing='any', special='any'):
        ''' Remove a set of consonants matching certain parameters from this language ''' 
        for consonant in self.get_matching_consonants(location=location, method=method, voicing=voicing, special=special):
            self.valid_consonants.remove(consonant)


    def create_word(self, number_of_syllables=2):
        ''' Generate a word in the language, using the appropriate phoneme frequencies '''
        syllables = []
        # Set to None so that the first onset knows that it's word-initial (no coda comes before the first syllable)
        coda = None

        for i in xrange(number_of_syllables):            
            syllable_position = self.get_syllable_position(current_syllable=i, total_syllables=number_of_syllables)

            onset = self.choose_valid_onset(previous_coda=coda, syllable_position=syllable_position)
            coda  = self.choose_valid_coda(onset=onset, syllable_position=syllable_position)

            nucleus = self.choose_valid_nucleus(onset=onset, coda=coda, syllable_position=syllable_position)

            syllables.append(Syllable(onset=onset.phoneme_ids, nucleus=nucleus.phoneme_ids, coda=coda.phoneme_ids))

        return self.orthography.phon_to_orth(word=Word(syllables=syllables))


    def choose_valid_onset(self, previous_coda, syllable_position):
        ''' Business logic for determining whether an onset is valid, given the previous coda and other constraints '''

        # At the beginning of the word, any onset is valid
        if previous_coda is None:
            return weighted_random(self.probabilities['onset'])
        # Otherwise, if the previous coda was complex, we'll assign an empty onset
        elif previous_coda.is_complex():
            return p.data.empty_onset
        # No onsets for syllables in the middle of the word if the previous syllable has a coda
        elif syllable_position == 1 and not previous_coda.is_empty():
            return p.data.empty_onset
        # If this onset follows a coda (even a simple one), there is a chance that we'll ignore the
        # force an empty onset - this helps with readability, especially in longer words
        elif not previous_coda.is_empty() and chance(FORCE_EMPTY_ONSET_AFTER_ANY_CODA_CHANCE):
            return p.data.empty_onset

        # Otherwise, generate an onset with some restrictions
        # Stash the previous coda's last phoneme in case we need to check it multiple times
        previous_coda_last_phoneme = previous_coda.phoneme_ids[-1]

        # Loop through and generate onsets until one matches all criteria
        while True:
            onset = weighted_random(self.probabilities['onset'])
            # Can't start one syllable off with the same phoneme that the previous ended with
            if onset.phoneme_ids[-1] == previous_coda_last_phoneme:
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
            return p.data.empty_coda

        # Loop through until a valid coda is generated
        while True:
            coda = weighted_random(self.probabilities['coda'])
            # No /l/ or /r/ in codas when the onset contains one of these
            if onset.has_any_phoneme( (221, 224) ) and coda.has_any_phoneme( (221, 224) ):
                continue
            # Single syllable words without an onset must have a coda
            if syllable_position == -1 and coda.is_empty():
                continue

            # If the coda has made it through the gauntlet, break out of the loop and return it
            return coda


    def choose_valid_nucleus(self, onset, coda, syllable_position):
        ''' Choose a valid vowel given an onset, coda, and syllable position '''

        # TODO - ideally this would pick a "master proibability dict"
        # to choose from, and THEN run through the gauntlet of rules/
        # Currently if syllable_position == 1, it will choose a monophthong
        # but won't apply any other rules outlined in the "while" loop

        # Diphthongs cannot occur in the middle of a word
        if syllable_position == 1:
            return weighted_random(self.nuclei_with_monophthong_probabilities)

        while True:
            # Generate the vowel based off of the combined weighings of the vowels surrounding it
            nucleus = weighted_random(self.probabilities['nucleus'])
            vowel = nucleus.phonemes[0]

            # A short vowel cannot occur if there is no consonant in the coda
            # if syllable_position == 2 and coda.is_empty() and vowel.manner == 'lax':
            #     continue
            # # Only short vowels can occur before /ng/
            # if coda.phoneme_ids[0] == 220 and vowel.manner != 'lax':
            #     continue

            # If the nucleus has made it through the gauntlet, break out of the loop and return it
            return nucleus


    def get_syllable_position(self, current_syllable, total_syllables):
        ''' Get the position of a syllable within a word
            - 1 = only 1 syllable in the word
            0   = word initial
            1   = middle
            2   = final
        '''
        if   total_syllables == 1:  return -1   # Only 1 syllable in the word
        elif current_syllable == 0: return 0    # On the first syllable
        elif current_syllable == \
             total_syllables - 1:   return 2    # On the last syllable
        else:                       return 1    # Otherwise, it's in the middle

    def is_common_syllable_component(self, target_syllable_component, phoneme_id, top_phoneme_level):
        ''' See if a syllable component is common in a language '''

        
        sorted_probabilities = sorted([(self.probabilities[target_syllable_component][component], component) 
                                            for component in self.probabilities[target_syllable_component]], reverse=True)
        for probability, component in sorted_probabilities[0:top_phoneme_level+1]:
            if component.has_any_phoneme(phoneme_id):
                return 1
        return 0


    def info_dump(self):
        ''' Summarize some basic information about the language and print it out '''
        for text in self.log:
            print text

        table_data = []

        for component in ('onset', 'coda', 'nucleus'):
            probabilities = sorted(((self.probabilities[component][phoneme], phoneme) 
                for phoneme in self.probabilities[component].keys()), reverse=True)
            
            table_data.append('{0: >4} {1}'.format(perc, phoneme.get_string()) for perc, phoneme in probabilities)

        # Print valid onsets, codas, and nuclei
        print("{: <12} {: <12} {: <12}".format('Onsets', 'Codas', 'Nuclei'))
        for i, row in enumerate(itertools.izip_longest(*table_data, fillvalue="")):
            print("{: <12} {: <12} {: <12}".format(*row))
            if i > 5: break

        print ''


def weighted_random(choices):
    ''' http://stackoverflow.com/questions/2570690/python-algorithm-to-randomly-select-a-key-based-on-proportionality-weight '''
    # Takes a dict of choice:weight pairs as input

    # ------ Temp fix to preserve random seed - Iteration order in a dict is not consistent ------- #
    choices_ordered = [(k, v) for k, v in choices.iteritems()]
    choices_ordered.sort()
    # ------ End temp fix to preserve random seed ------------------------------------------------- #

    r = random.uniform(0, sum(choices.itervalues()))
    s = 0.0
    for k, w in choices_ordered:
        s += w
        if r < s: return k
    return k


if __name__ == '__main__':
    print ''

    seed = roll(0, 32000)
    print ' -- Running with random seed', seed 
    random.seed(seed)

    t = Language()
    t.generate_language_properties()

    t.info_dump()

    # t.orthography.get_alphabet()

    for i in xrange(12):
        print '{: <14} {: <14} {: <14}'.format(t.create_word(number_of_syllables=1),
                                               t.create_word(number_of_syllables=2),
                                               t.create_word(number_of_syllables=3))

    print ''

