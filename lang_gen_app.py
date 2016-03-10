from __future__ import division, unicode_literals
import os
import urllib
import random

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


import lang_gen

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

LANGUAGE_ADJECTIVES = (
    'noble', 'dignified', 'distinguished', 'extraordinary', 'great', 'magnificent', 'remarkable',
    'magnanimous', 'meritorious', 'esteemed', 'eminent', 'illustrious', 'renowned', 'venerable',
    'baffling', 'curious', 'mysterious', 'cryptic', 'enigmatic', 'inscrutiable', 'peculiar', 'marvelous',
    'wondrous'
)

DESC_1_ADJECTIVES = ['captivating', 'stunning', 'breathtaking', 'fascinating']

DESC_1_NOUNS = ['specimen', 'tongue', 'discovery']

def new_language():
    language = lang_gen.Language()
    language.generate_language_properties()

    name = language.create_word(meaning='Name of language', number_of_syllables=2)
    vocabulary = language.get_sample_vocabulary_words()
    # Split into 2 equal sublists for display
    vocab1 = vocabulary[:int(len(vocabulary)/2)]
    vocab2 = vocabulary[int(len(vocabulary)/2):]

    compound_words = language.get_sample_word_sets()

    onset_description, coda_description = language.describe_syllable_level_rules()

    language_adjective = random.choice(LANGUAGE_ADJECTIVES)
    language_description = '{0} {1}'.format(random.choice(DESC_1_ADJECTIVES), random.choice(DESC_1_NOUNS))

    return language, name, vocab1, vocab2, compound_words, onset_description, coda_description, language_adjective, language_description


class MainPage(webapp2.RequestHandler):

    def get(self):
        language, name, vocab1, vocab2, compound_words, onset_description, coda_description, language_adjective, language_description = new_language()
        
        template_values = {
            'seed': lang_gen.seed,
            'name': name,
            'adjective': language_adjective,
            'language_description': language_description,
            'vocab1': vocab1,
            'vocab2': vocab2,
            'compound_words': compound_words,
            'descriptions': [onset_description, coda_description],
            'number_of_consonants': len(language.valid_consonants),
            'number_of_vowels':len(language.probabilities['nucleus']),
            'consonants': sorted([language.orthography.mapping[consonant.id_].get_description() for consonant in language.valid_consonants], key=lambda desc_tuple: desc_tuple[0]),
            'vowels': sorted([language.orthography.mapping[vowel.id_].get_description() for vowel in language.valid_vowels], key=lambda desc_tuple: desc_tuple[0]),
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)