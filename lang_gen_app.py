import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
import lang_gen


def new_language():
    t = lang_gen.Language()
    t.generate_language_properties()

    name = t.create_word(meaning='Name of language', number_of_syllables=2)
    words = t.get_sample_word_sets()
    
    return name, words, t.log

class MainPage(webapp2.RequestHandler):
    def get(self):
        # self.response.write(MAIN_PAGE_HTML)
        name, words, log = new_language()
        
        template_values = {
          'name': name, 
          'words': words,
          'text_log': log
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