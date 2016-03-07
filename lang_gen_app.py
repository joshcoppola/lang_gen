from __future__ import division, unicode_literals
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


import lang_gen

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def new_language():
    language = lang_gen.Language()
    language.generate_language_properties()

    name = language.create_word(meaning='Name of language', number_of_syllables=2)
    words = language.get_sample_word_sets()

    onset_description, coda_description = language.describe_syllable_level_rules()

    return language, name, words, onset_description, coda_description


class MainPage(webapp2.RequestHandler):

    def get(self):
        language, name, words, onset_description, coda_description = new_language()
        
        template_values = {
            'name': name,
            'words': words,
            'descriptions': [onset_description, coda_description],
            'phoneme_info': '{0} has {1} consonants and {2} vowels'.format(name, len(language.valid_consonants), len(language.probabilities['nucleus'])),
            'consonants': sorted([language.orthography.mapping[consonant.id_].get_description() for consonant in language.valid_consonants], key=lambda desc_tuple: desc_tuple[0]),
            'vowels': sorted([language.orthography.mapping[vowel.id_].get_description() for vowel in language.valid_vowels], key=lambda desc_tuple: desc_tuple[0]),
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class Guestbook(webapp2.RequestHandler):
    def post(self):
        self.response.write('<html><body>You wrote:<pre>')
        self.response.write(cgi.escape(self.request.get('content')))
        self.response.write('</pre></body></html>')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
], debug=True)