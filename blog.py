import datetime
import os

from utils import *

import webapp2
import jinja2

from google.appengine.ext import db
from google.appengine.api import mail

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class User(db.Model):
    email = db.StringProperty(required=True)
    username = db.StringProperty()
    register_time = db.DateTimeProperty(auto_now_add=True)
    password = db.StringProperty(required=True)
    items_holds = db.ListProperty(db.Key)
    items_wanted = db.ListProperty(db.Key)
    

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


class Signin(BaseHandler):
    def get(self):
        self.render("signin-form.html")

    def post(self):
        have_error = False
        email = self.request.get('email')
        pwd = self.request.get('password')
        params = dict(email = email, password = pwd)
        user = None

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True
        elif not valid_password(pwd):
            params['error_password'] = "Invalid password."
            have_error = True
        else:
            q =  db.Query(User).filter('email =', email)
            user = q.fetch(1)
            if user:
                if pwd != user[0].password:
                    params['error_password']= "Password incorrect!"
                    have_error = True
            else:
                params['error_email'] = "User doesn't exist."
                have_error = True
        
        if have_error:
            self.render('signin-form.html', **params)
        else:
            self.redirect('/welcome?username=' + (email.split('@'))[0])

class Signup(BaseHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        domain = self.request.get('domain')
        params = dict(username = username, domain=domain)

        if not valid_username(username):
            params['error_username'] = "That's not a valid email."
            have_error = True
        elif db.Query(User).filter('username =', username).count(1)==1:
            params['error_username'] = "User already exists."
            have_error = True
        
        if have_error:
            self.render('signup-form.html', **params)
        else:
            pwd = id_generator()
            user = User(username = username, email = username+domain, password = pwd)
            user.put()
            registration_msg = 'Your password is %s' % pwd
            print registration_msg
            print username+domain
            message = mail.EmailMessage(sender='Exchange-JP Team <xingxiaoxiong@gmail.com>',
                                        to=username+domain,
                                        subject='Welcome to Exchange-JP',
                                        body=registration_msg)
            message.send()
            self.redirect('/welcome?username=' + username)


class Welcome(BaseHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/signup')

app = webapp2.WSGIApplication([('/signup', Signup),
                               ('/signin', Signin),
                               ('/welcome', Welcome)],
                              debug=True)
