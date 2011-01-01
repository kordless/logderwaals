#!/usr/bin/env python
#
# Copyright 2010 Loggly Inc.
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
#
import cgi, os, datetime, time
import logging, loggly
import urllib2, base64, urllib
from django.utils import simplejson 
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

# variable things
appengineurl = 'logderwaals.appspot.com'
logglyaccount = 'geekceo.loggly.com'

# grab data for a geckoboard graph object
class GraphHandler(webapp.RequestHandler):
  def get(self):
    q = self.request.get('q')
    if q == "": q = "*"

    # limit the query to just the web server's input
    q = q + " AND inputname:loggly_web"
    logging.info("executing a query to loggly for: %s" % q)
    query = urllib.quote(q)

    # auth stuff
    username = 'kordless'
    password = 'password'
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

    # query last day and convert to json
    request = urllib2.Request("http://%s/api/facets/date?q=%s&from=NOW-1DAY&until=NOW" % (logglyaccount, query))
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    json_result = simplejson.loads(result.read())

    # sort dict, then shovel it over to the template
    stuff = []
    for item in sorted(json_result['data'].items()):
       stuff.append(item)
    from_date = stuff[0][0] #first date
    until_date = stuff[-1][0] #last date
    template_values = {'stuff': stuff, 'from_date': from_date, 'until_date': until_date}
    path = os.path.join(os.path.dirname(__file__), 'templates/graph.xml')
    self.response.headers['Content-Type'] = 'text/xml'
    self.response.out.write(template.render(path, template_values))  
  def post(self):
    self.get()

# grab data for a geckoboard meter object
class MeterHandler(webapp.RequestHandler):
  def get(self):
    q = self.request.get('q')
    if q == "": q = "*"
   
    # limit the query to just the web server's input
    q = q + " AND inputname:loggly_web"
    logging.info("executing a query to loggly for: %s" % q)
    query = urllib.quote(q)

    # auth stuff
    username = 'kordless'
    password = 'password'
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

    # query last hour
    request = urllib2.Request("http://%s/api/facets/date?q=%s&from=NOW-1HOUR&until=NOW" % (logglyaccount, query))
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    stuff = simplejson.loads(result.read())
    numfound = stuff['numFound'] 
   
    # query last day  
    request = urllib2.Request("http://%s/api/facets/date?q=%s&from=NOW-1DAY&until=NOW" % (logglyaccount, query))
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    stuff = simplejson.loads(result.read())
    numfoundlastday = stuff['numFound'] 

    # shovel it over to the template
    template_values = {'numfound': numfound, 'numfoundlastday': numfoundlastday}
    path = os.path.join(os.path.dirname(__file__), 'templates/meter.xml')
    self.response.headers['Content-Type'] = 'text/xml'
    self.response.out.write(template.render(path, template_values))  
  def post(self):
    self.get()


class MainPage(webapp.RequestHandler):
  def get(self):
    logging.info("a noob is knocking")
    self.response.out.write("This is a Loggly Gecko mashup example.  Try viewing some raw XML data: <br/><br/><a href='/meter?q=404'>a meter for '404' error codes</a><br/><br/> <a href='/graph?q=wiki AND POST'>a graph for wiki edits</a>")
  def post(self):
    self.get()


application = webapp.WSGIApplication( [('/', MainPage), ('/meter', MeterHandler), ('/graph', GraphHandler)], debug=True) 

def main():
  # set up logging to Loggly and log the time on the appengine box
  hoover = loggly.LogglyLogger('http://logs.loggly.com/inputs/d83ef1fb-5214-4106-9d32-6956201c29ce', logging.INFO)
  rightnow = time.time()
  logging.info('time=%s' % (rightnow) )
  
  run_wsgi_app(application)


if __name__ == "__main__":
  main()

