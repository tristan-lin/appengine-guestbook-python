#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2
import datetime

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GUESTBOOK_NAME = 'default_bill_note-1'
QUOTA_PER_DAY = 7000


# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)


# [START greeting]
class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    amount = ndb.StringProperty(indexed=True)
    category = ndb.StringProperty(indexed=True)
    method = ndb.StringProperty(indexed=True)
    dateR = ndb.StringProperty(indexed=True)
# [END greeting]




# Define the data structure we save in datastore
def template_values(user,greetings,guestbook_name,url,url_linktxt,today_sum,week_sum,month_cost):
	t={
	"user":user,
	"greetings":greetings,
	"guestbook_name":guestbook_name,
	"url":url,
    "url_linktext":url_linktxt,
    "sum": {"today":today_sum,"week":week_sum,"month_cost":month_cost}}
	return t

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        d=datetime.datetime.now()
        week_ago= d - datetime.timedelta(days=7)
        
        week_entity=Greeting.query(Greeting.dateR > week_ago.strftime('%Y-%m-%d')).fetch()
        month_entity=Greeting.query(Greeting.dateR >= datetime.date(d.year, d.month, 1).strftime('%Y-%m-%d')).fetch()
        today_entity=Greeting.query(Greeting.dateR == datetime.datetime.now().strftime('%Y-%m-%d')).fetch()
        
        sum_week_int = 0
        sum_today_int = 0
        sum_month_int = 0
        try:
            for x in week_entity:
                sum_week_int = sum_week_int + int(x.amount)
            for x in today_entity:
                sum_today_int = sum_today_int + int(x.amount)
            for x in month_entity:
                sum_month_int = sum_month_int + int(x.amount)

            
            sum_week_int = QUOTA_PER_DAY*7 - sum_week_int
            sum_today_int = QUOTA_PER_DAY - sum_today_int
        except:
            sum_week_int = 0
            sum_today_int = 0
            sum_month_int = 0
        
        
        user = users.get_current_user()
        
        try:
            if users.get_current_user().email()=="YOUR_GMAIL@gmail.com" :
                t=template_values(user,greetings,urllib.quote_plus(guestbook_name),users.create_logout_url(self.request.uri),'Logout',sum_today_int,sum_week_int,sum_month_int)
            else:
                url = users.create_login_url(self.request.uri)
                url_linktext = 'Login'
                t=template_values("","","",url,url_linktext,0,0,0)
        except:
                url = users.create_login_url(self.request.uri)
                url_linktext = 'Login'
                t=template_values("","","",url,url_linktext,0,0,0)

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(t))
# [END main_page]


# [START guestbook]
class Guestbook(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.content = self.request.get('content')
        greeting.amount = self.request.get('amount')
        greeting.category = self.request.get('category')
        greeting.dateR = self.request.get('date')
        greeting.method = self.request.get('method')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))
# [END guestbook]


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
], debug=True)
# [END app]
