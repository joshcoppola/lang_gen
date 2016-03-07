
from __future__ import division, unicode_literals
import random
from random import randint as roll
from collections import namedtuple, OrderedDict
from copy import deepcopy

import itertools

import phonemes as p
import orthography
from helpers import weighted_random, chance, clamp, join_list

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
PLOSIVE_TYPES = OrderedDict({
    'unaspirated': 50,
    'aspirated': 35,
    'aspirated and unaspirated': 25
})

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
DROP_RANDOM_MONOPHTHONG_CHANCE = 15
DROP_RANDOM_DIPHTHONG_CHANCE   = 25

MIN_NUM_VOWELS = 4

# -- For complex syllable components, their probability is reduced by these amounts -- #
COMPLEX_ONSET_PROBABILITY_MULTIPLIER = .35

COMPLEX_CODA_PROBABILITY_MULTIPLIER = .35

DIPHTHONG_PROBABILITY_MULTIPLIER = .40

# The probability uses a function that can occasionally generate very high numbers.
# These set the minimum / maximum possible value (with default parameters, it's common 
# to see the highest probabilities at 200 or so, but spikes as high as 1000+ aren't uncommon)
MIN_COMPONENT_PROBABILITY = 1
MAX_COMPONENT_PROBABILITY = 500

# This is the probability that an empty onset will be forced after a syllable with any coda
# Otherwise, certain languages may have high probabilities of big multi-consonant clusters
# which are valid but hard to read (especially in 3+ syllable words)
FORCE_EMPTY_ONSET_AFTER_ANY_CODA_CHANCE = 35

COMPOUND_WORD_DROP_PREVIOUS_CODA_CHANCE = 25
COMPOUND_WORD_DROP_ONSET_CHANCE = 25

# The maximum amount of phonemes a word can be to have the generator consider including
# the entire word (not just the root) into the compound word
MAX_COMPOUND_WORD_PHONEMES_PER_SECTION = 4

# How many syllables a compound word can become, before the generator forces a sub-word
# to become truncated (using only the word's root)
MAX_COMPOUND_WORD_SYLLABLES_BEFORE_FORCE_USING_WORD_ROOT = 2

# When generating a compound word, the chance that it will try to use the entire sub-word
# as part of the compound word, if it meets all other criteria
USE_FULL_WORD_FOR_COMPOUND_WORD_CHANCE = 60

# A data structure containing phoneme #s for different parts of the syllable
# Syllable = namedtuple('Syllable', ['onset', 'nucleus', 'coda'])

class Syllable:
    def __init__(self, onset, nucleus, coda):
        self.onset = onset
        self.nucleus = nucleus
        self.coda = coda

    def get_components(self):
        return (self.onset, self.nucleus, self.coda)

    def number_of_non_empty_components(self):
        ''' Find how many non-empty components a syllable has '''
        return sum((not component.is_empty()) for component in self.get_components())

    def number_of_phonemes(self):
        return sum((len(component.phoneme_ids) for component in self.get_components() if not component.is_empty()))

class Word:
    def __init__(self, meaning, language, syllables, etymology=None):
        self.meaning = meaning
        self.language = language
        self.syllables = syllables

        # Writing as a generator comprehension for speed, at the cost of readability?
        self.phoneme_ids =  tuple(phoneme_id 
                                    for syllable in syllables
                                        for component in syllable.get_components()
                                            for phoneme_id in component.phoneme_ids)
        
        self.root = self.set_root()

        self.etymology = etymology

    def __len__(self):
        return len(self.phoneme_ids)

    def __str__(self):
        return self.language.orthography.phon_to_orth(word=self)

    def number_of_non_empty_phonemes(self):
        return len([phoneme_id for phoneme_id in self.phoneme_ids if phoneme_id < 300])

    def set_root(self):
        ''' Determine the "root" syllable of a word, currently by choosing the syllable
            with the most non-empty phonemes '''

        phonemes_per_syllable = ((syllable.number_of_phonemes(), syllable) for syllable in self.syllables)
        chosen_syllable = sorted(phonemes_per_syllable, reverse=True)[0][1]

        return self.create_syllable_from_nearby_phonemes(chosen_syllable)

    def create_syllable_from_nearby_phonemes(self, syllable):
        ''' When looking at a root syllable, sometimes the word itself may have consonant phonemes
            before or after the root syllable, although the root syllable is considered to have an
            empty onset or coda. This function will create a new special "root" syllable which may
            contain some of the phonemes from surrounding syllables, making the "root" appear to 
            compose a larger part of the word '''

        s_index = self.syllables.index(syllable)

        new_syllable_info = {'onset': syllable.onset, 'nucleus': syllable.nucleus, 'coda': syllable.coda}

        # ---------- Word roots can assimilate the last consonant of the previous coda ---------- #
        if syllable.onset.is_empty() and s_index > 0 and (not self.syllables[s_index - 1].coda.is_empty()):
            last_phoneme_of_previous_coda = self.syllables[s_index - 1].coda.phoneme_ids[-1]
            # Get the onset which matches the last phoneme from the previous coda
            potential_onset = p.data.get_component_by_phoneme_ids(syllable_component_type='onset', 
                                                                    phoneme_ids=tuple([last_phoneme_of_previous_coda]))
            # Make sure that the new onset is valid in this language
            if potential_onset is not None and potential_onset in self.language.probabilities['onset']:
                new_syllable_info['onset'] = potential_onset

        # ---------- Word roots can also assimilate the first consonant of the preceding coda ---------- #
        if syllable.coda.is_empty() and s_index < len(self.syllables) - 1 and (not self.syllables[s_index + 1].onset.is_empty()):
            first_phoneme_of_next_onset = self.syllables[s_index + 1].onset.phoneme_ids[0]
            # Get the coda which matches the first phoneme from the precedinbg onset
            potential_coda = p.data.get_component_by_phoneme_ids(syllable_component_type='coda', 
                                                                    phoneme_ids=tuple([first_phoneme_of_next_onset]))
            # Make sure that the new coda is valid in this language
            if potential_coda is not None and potential_coda in self.language.probabilities['coda']:
                new_syllable_info['coda'] = potential_coda

        return Syllable(onset=new_syllable_info['onset'], nucleus=new_syllable_info['nucleus'], coda=new_syllable_info['coda'])


    def get_phonemes(self):
        ''' A generator which returns the phoneme id and position within the syllable
            for all phonemes in the word, in addition to the syllable component and whether
            or not this particular position is at a boundary between syllables '''
        phoneme_index = -1

        for syllable_number, syllable in enumerate(self.syllables):
            # Each component in the syllable has one or more phoneme ids
            for component_index, component in enumerate(syllable.get_components()):
                # A syllable component can have more than one phoneme (/spr/, /rt/, etc)
                for phoneme_position_within_component, phoneme_id in enumerate(component.phoneme_ids):
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

    def desc_etymology(self):
        if self.etymology:
            desc_list = ['{0} ("{1}")'.format(root_word, english_morpheme) for (root_word, english_morpheme) in self.etymology]
            desc = 'from {0}'.format(join_list(desc_list))

        else:
            desc = '(unknown origin)'

        return desc


class Language:
    def __init__(self):
        self.properties = {}

        self.valid_consonants = {c for c in p.CONSONANTS if c.id_ < 300}
        self.valid_vowels = set([])

        self.probabilities = { 'onset': OrderedDict(), 'coda': OrderedDict(), 'nucleus': OrderedDict(), 'nucleus_monophthong': OrderedDict() }

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


        ## ------------------------- Log some info ---------------------------- ##
        onset_description, coda_description = self.describe_syllable_level_rules()
        self.log.extend( [onset_description, coda_description] )

        self.log.append( 'No onset mutiplier: {0}'.format(self.properties['no_onset_multiplier']) )
        self.log.append( 'No coda mutiplier: {0}'.format(self.properties['no_coda_multiplier']) )

        self.log.append( 'Consonants: {0}; Vowels: {1}\n'.format(len(self.valid_consonants), len(self.probabilities['nucleus'])) )

        ## -------------------------- Set orthography -------------------------------- ##

        self.orthography = orthography.Orthography(parent_language=self)


    def generate_valid_onsets(self):
        ''' Contains some logic for choosing valid onsets for a language, by picking systematic features to disallow '''
        invalid_consonants = self.get_matching_consonants(voicing=self.properties['onset_voicing_restriction'],
                                                          exclude_matches=self.properties['invert_onset_voicing_restriction'])

        for onset in p.data.all_syllable_components['onset']:
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

        for coda in p.data.all_syllable_components['coda']:
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
        for nucleus in p.data.all_syllable_components['nucleus']:
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
            random_new_nucleus = random.choice(tuple(p.data.all_syllable_components['nucleus']))
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

        if most_probable_vowel_nucleus != most_probable_monophthong_nucleus:
            self.log.append( "Flipping {0} with {1}".format(most_probable_vowel_nucleus, most_probable_monophthong_nucleus) )
            # Flip the probabilities
            self.probabilities['nucleus'][most_probable_monophthong_nucleus], self.probabilities['nucleus'][most_probable_vowel_nucleus] = \
                self.probabilities['nucleus'][most_probable_vowel_nucleus], self.probabilities['nucleus'][most_probable_monophthong_nucleus]

        # ----------- Cleanup - Build a list of just nuclei with monophthongs for later use  --------------- #

        self.probabilities['nucleus_monophthong'] = {nucleus: self.probabilities['nucleus'][nucleus]
                                                        for nucleus in self.probabilities['nucleus'] 
                                                            if not nucleus.phonemes[0].is_diphthong() }

        # ---------------------------------------- End Cleanup --------------------------------------------- #

        # ------------- Put aside a set of the vowels contained within the syllable components ------------- #

        for nucleus in self.probabilities['nucleus'].keys():
            self.valid_vowels.add(nucleus.phonemes[0])

    def get_component_probability(self, component_type, component):
        ''' Once a syllable component (onset, coda, or nucleus) has been generated and needs to be 
            added to the language, this method handles generating the probability and adding it '''

        probability = None

        # ------------------------------ Onset ------------------------------ #
        if component_type == 'onset':
            if not component.is_complex():  probability = int(random.lognormvariate(3, 1.2)) 
            elif   component.is_complex():  probability = int(random.lognormvariate(3, 1.2) * COMPLEX_ONSET_PROBABILITY_MULTIPLIER)

        # ------------------------------ Coda ------------------------------- #
        elif component_type == 'coda':
            if not component.is_complex():  probability = int(random.lognormvariate(3, 1.2))
            elif   component.is_complex():  probability = int(random.lognormvariate(3, 1.2) * COMPLEX_CODA_PROBABILITY_MULTIPLIER)

        # ------------------------------ Nucleus ----------------------------- #
        elif component_type == 'nucleus':
            vowel = component.phonemes[0]
            
            if not vowel.is_diphthong():    probability = int(random.lognormvariate(3, 1.2))
            elif   vowel.is_diphthong():    probability = int(random.lognormvariate(3, 1.2) * DIPHTHONG_PROBABILITY_MULTIPLIER)

        return clamp(minimum=MIN_COMPONENT_PROBABILITY, num=probability, maximum=MAX_COMPONENT_PROBABILITY)


    def create_syllable_rule_description(self, syllable_component, component_cannot_be_complex,
                                        voicing_restriction, voicing_restriction_exclusion):
        ''' Placeholder function to describe syllable-level phonemic restrictions '''


        # ------------------ Describe voicing restrictions, if any ----------------- #
        if voicing_restriction is None:
            voicing_description = 'have no voicing restrictions'

        else:
            voicing_type = {0:'unvoiced', 1:'voiced'}[voicing_restriction]

            if voicing_restriction_exclusion == 1:  voicing_description = 'only {0} consonants can appear'.format(voicing_type)
            else:                                   voicing_description = '{0} consonants cannot appear'.format(voicing_type)

        # --------------------------- Describe complexity -------------------------- #
        complexity_description = {0:'can be simple or complex', 1:'cannot be complex'}[component_cannot_be_complex]

        return 'Syllable {0}s {1}, and {2}'.format(syllable_component, complexity_description, voicing_description)


    def describe_syllable_level_rules(self):
        ''' Describes any rules for forming an onset or coda in this language '''

        onset_description = self.create_syllable_rule_description(syllable_component='onset',
                                            component_cannot_be_complex=self.properties['no_complex_onsets'],
                                            voicing_restriction=self.properties['onset_voicing_restriction'],
                                            voicing_restriction_exclusion=self.properties['invert_onset_voicing_restriction'])

        coda_description = self.create_syllable_rule_description(syllable_component='coda',
                                            component_cannot_be_complex=self.properties['no_complex_codas'],
                                            voicing_restriction=self.properties['coda_voicing_restriction'],
                                            voicing_restriction_exclusion=self.properties['invert_coda_voicing_restriction'])

        return onset_description, coda_description


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
            return weighted_random(self.probabilities['nucleus_monophthong'])

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


    def get_word(self, meaning):
        ''' Gets a word from the dictionary, creating it if it doesn't exist '''
        if meaning not in self.vocabulary:
            self.create_word(meaning=meaning, number_of_syllables=random.choice((1, 2)))

        return self.vocabulary[meaning]


    def create_word(self, meaning, etymology=None, number_of_syllables=2):
        ''' Generate a word in the language, using the appropriate phoneme frequencies '''
        syllables = []
        # Set to None so that the first onset knows that it's word-initial (no coda comes before the first syllable)
        coda = None

        for i in xrange(number_of_syllables):            
            syllable_position = self.get_syllable_position(current_syllable=i, total_syllables=number_of_syllables)

            onset = self.choose_valid_onset(previous_coda=coda, syllable_position=syllable_position)
            coda  = self.choose_valid_coda(onset=onset, syllable_position=syllable_position)

            nucleus = self.choose_valid_nucleus(onset=onset, coda=coda, syllable_position=syllable_position)

            syllables.append(Syllable(onset=onset, nucleus=nucleus, coda=coda))

        word = Word(meaning=meaning, language=self, syllables=syllables)

        # Add to vocabulary if it has a meaning
        if meaning:
            self.vocabulary[meaning] = word

        return word


    def create_compound_word(self, meaning, english_morphemes):
        ''' Takes one or more english morphemes in a string format (separated by spaces), 
            makes sure they're in the dictionary, gets the roots of each, and joins them 
            together into a compound word '''

        syllables = []
        etymology = []

        for i, english_morpheme in enumerate(english_morphemes.split()):
            # Handles creating the word in the dictionary, if it doesn't already exist
            original_word = self.get_word(meaning=english_morpheme)

            # If the word is short enough, the entire thing may be appended
            if original_word.number_of_non_empty_phonemes() <= MAX_COMPOUND_WORD_PHONEMES_PER_SECTION \
                        and len(syllables) <= MAX_COMPOUND_WORD_SYLLABLES_BEFORE_FORCE_USING_WORD_ROOT\
                        and chance(USE_FULL_WORD_FOR_COMPOUND_WORD_CHANCE):
                # !! Make sure to make a copy of the original word's syllables or weird stuff happens. Deepcopy appears to not be
                # necessary... but it's probably a good idea
                syllables = self.trim_syllables(current_syllables=deepcopy(original_word.syllables), all_current_syllables=syllables)

            # If the word is long, use the word's root
            else:
                # !! Make sure to make a copy of the original word's root. Technically not necessary... but probably a good idea
                syllables = self.trim_syllables(current_syllables=[deepcopy(original_word.root)], all_current_syllables=syllables)

            # Append the full original word so it can be tracked in the etymology
            etymology.append((original_word, english_morpheme))

        # Create the word
        compound_word = Word(meaning=meaning, language=self, syllables=syllables, etymology=etymology)

        # Add to dictionary
        self.vocabulary[english_morphemes] = compound_word

        return compound_word

    def trim_syllables(self, current_syllables, all_current_syllables):
        ''' Take a syllable, get its root, and add it to all current syllables.
            Makes any adjustments necessary to the root, including perhaps dropping parts of
            previous syllables (not currently implemented) '''

        # --- Make sure the current syllable's first phoneme is not the same as the previous syllable's last phoneme --- #
        if len(all_current_syllables) and all_current_syllables[-1].coda.phoneme_ids[-1] == current_syllables[0].onset.phoneme_ids[0]:
            # Keep the syllable the same, but with an empty onset
            current_syllables = self.pop_and_replace_with_onset(current_syllables=current_syllables, new_onset=p.data.empty_onset)
            all_current_syllables.extend(current_syllables)

        # -- One the rare case there is an empty coda followed by an empty onset, add a consonant between them --- #
        elif len(all_current_syllables) and all_current_syllables[-1].coda == p.data.empty_coda \
                                        and current_syllables[0].onset == p.data.empty_onset:

            # Choose an onset from the list of this language's valid onsets. (Syllable position shouldn't matter for picking
            # an onset, but here we're choosing a value of 1 (middle of word) anyway. Loop to ensure an empty onset is not chosen!
            dividing_onset = p.data.empty_onset
            while dividing_onset != p.data.empty_onset:
                dividing_onset = self.choose_valid_onset(previous_coda=all_current_syllables[-1].coda, syllable_position=1)

            current_syllables = self.pop_and_replace_with_onset(current_syllables=current_syllables, new_onset=dividing_onset)
            all_current_syllables.extend(current_syllables)

        # --- If the previous coda is not complex, and the current onset is not complex, join without truncating anything --- #
        elif len(all_current_syllables) \
            and chance(50) \
            and (not all_current_syllables[-1].coda.is_complex()) \
            and (not current_syllables[0].onset.is_complex()):

            all_current_syllables.extend(current_syllables)

        # --- If the previous coda is not empty, and the current onset is not empty, join after truncating current syllable's onset --- #
        elif len(all_current_syllables) \
                and (not all_current_syllables[-1].coda.is_empty()) \
                and (not current_syllables[0].onset.is_empty()):

            current_syllables = self.pop_and_replace_with_onset(current_syllables=current_syllables, new_onset=p.data.empty_onset)
            all_current_syllables.extend(current_syllables)

        # --- Otherwise, join without truncating anything --- #
        else:
            all_current_syllables.extend(current_syllables)


        return all_current_syllables

    def pop_and_replace_with_onset(self, current_syllables, new_onset):
        ''' Specific helper method to avoid code duplication '''
        syllable_to_change = current_syllables.pop(0)
        worked_syllable = Syllable(onset=new_onset, nucleus=syllable_to_change.nucleus, coda=syllable_to_change.coda)
        current_syllables.insert(0, worked_syllable)

        return current_syllables

    def info_dump(self):
        ''' Summarize some basic information about the language and print it out '''
        for text in self.log:
            print text

        table_data = []

        for component_type in ('onset', 'coda', 'nucleus'):
            probabilities = sorted(((self.probabilities[component_type][syllable_component], syllable_component) 
                for syllable_component in self.probabilities[component_type].keys()), reverse=True)
            
            table_data.append('{0: >4} {1}'.format(perc, syllable_component) for perc, syllable_component in probabilities)

        # Print valid onsets, codas, and nuclei
        print("{: <12} {: <12} {: <12}".format('Onsets', 'Codas', 'Nuclei'))
        for i, row in enumerate(itertools.izip_longest(*table_data, fillvalue="")):
            print("{: <12} {: <12} {: <12}".format(*row))
            if i > 5: break

        print ''


    def get_sample_word_sets(self):
        sample_compound_words = (
            self.create_compound_word(meaning='black mountain', english_morphemes='black mountain'),
            self.create_compound_word(meaning='blue mountain', english_morphemes='blue mountain'),
            self.create_compound_word(meaning='black woods', english_morphemes='black woods'),
            self.create_compound_word(meaning='blue woods', english_morphemes='blue woods'),
            self.create_compound_word(meaning='long river', english_morphemes='long river'),
            self.create_compound_word(meaning='blue river', english_morphemes='blue river'),
            self.create_compound_word(meaning='black river', english_morphemes='black river'),
            self.create_compound_word(meaning='calm harbor', english_morphemes='calm harbor'),
            self.create_compound_word(meaning='great river', english_morphemes='great river'),
            self.create_compound_word(meaning='red island', english_morphemes='red island'),
            self.create_compound_word(meaning='red river', english_morphemes='red river')
        )

        # formatted_words = ['{0} "{1}" {2}'.format(word, word.meaning, word.desc_etymology()) for word in sample_compound_words]

        return sample_compound_words

    def get_sample_vocabulary_words(self):

        sample_words = ['city', 'house', 'teacher', 'student', 'lawyer', 'doctor', 'patient', 'waiter', 'secretary',
                        'priest', 'police', 'army', 'soldier', 'artist', 'author', 'manager', 'reporter', 'actor',
                        'hat', 'dress', 'shirt', 'pants', 'shoes', 'coat', 'son', 'daughter', 'mother', 'father' 'baby',
                        'man', 'woman', 'brother', 'sister', 'king', 'queen', 'president', 'boy', 'girl', 'child', 'human',
                        'friend', 'cheese', 'bread', 'soup', 'cake', 'chicken', 'apple', 'banana', 'orange', 'lemon', 'corn',
                        'rice', 'oil', 'seed', 'table', 'chair', 'bed', 'dream', 'window', 'door', 'book', 'key', 'letter',
                        'note', 'bag', 'box', 'tool', 'dog', 'cat', 'fish', 'bird', 'cow', 'pig', 'mouse', 'horse']

        return [self.get_word(english_word) for english_word in random.sample(sample_words, 20)]


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
        print '{: <14} {: <14} {: <14}'.format(t.create_word(meaning="none", number_of_syllables=1),
                                               t.create_word(meaning="none", number_of_syllables=2),
                                               t.create_word(meaning="none", number_of_syllables=3))

    print ''


    sample_compund_words = (
        t.create_compound_word(meaning='black mountain', english_morphemes='black mountain'),
        t.create_compound_word(meaning='blue mountain', english_morphemes='blue mountain'),
        t.create_compound_word(meaning='black woods', english_morphemes='black woods'),
        t.create_compound_word(meaning='blue woods', english_morphemes='blue woods')
        )

    for word in sample_compund_words:
        print '{0} "{1}" {2}'.format(word, word.meaning, word.desc_etymology())

    print ''

