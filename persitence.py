from formbuilder import app, mongo
from flask import flash, g
import string, random, datetime
from .utils import *


import pprint
pp = pprint.PrettyPrinter()


def createUser(newUser):
    mongo.db.users.insert_one(newUser)
    return User(username=newUser['username'])



def isNewUserRequestValid(form):   
    if not ('username' in form and 'email' in form and 'password1' in form and 'password2' in form):
        flash("All fields are required", 'warning')
        return False
    if form['username'] != sanitizeString(form['username']):
        flash("Username not valid", 'warning')
        return False
    if User(username=form['username']):
        flash("Username not available", 'warning')
        return False
    if not User().isEmailAvailable(form['email']):
        return False
    if not isValidPassword(form['password1'], form['password2']):
        return False
    return True



class User(object):
    user = None

    def __new__(cls, *args, **kwargs):
        instance = super(User, cls).__new__(cls)
        if kwargs:
            if 'token' in kwargs:
                user = mongo.db.users.find_one({"token.token": kwargs['token']})
            else:
                if g.current_user and not g.current_user.isRootUser():
                    # rootUser can find any user. else only find users registered with this hostname.
                    kwargs['hostname']=g.hostname
                user = mongo.db.users.find_one(kwargs)
            if user:
                instance.user=dict(user)
            else:
                return None
        return instance

    
    def __init__(self, *args, **kwargs):
        pass


    def findAll(cls, *args, **kwargs):
        if not g.current_user.isRootUser():
            kwargs['hostname']=g.hostname
        if kwargs:
            return mongo.db.users.find(kwargs)
        return mongo.db.users.find()      
    

    def isEmailAvailable(cls, email):
        if not isValidEmail(email):
            flash("email address is not valid", 'error')
            return False
        if User(email=email):
            flash("email address not available", 'error')
            return False
        return True

    @property
    def data(self):
        return self.user

    @property
    def username(self):
        return self.user['username']

    @property
    def enabled(self):
        return self.user['enabled']
        
    @property
    def hostname(self):
        return self.user['hostname']

    
    def totalForms(self):
        print("username: %s" % self.username)
        forms = Form().findAll(author=self.username)
        return forms.count()


    def save(self):
        mongo.db.users.save(self.user)


    def isRootUser(self):
        if self.user['email'] in app.config['ROOT_ADMINS']:
            return True
        return False
    

    @property
    def token(self):
        return self.user['token']['token']


    def hasTokenExpired(self):
        token_age = datetime.datetime.now() - self.user['token']['created']
        if token_age.total_seconds() > app.config['TOKEN_EXPIRATION']:
            return True
        return False


    def setToken(self):
        token = getRandomString(length=48)
        while mongo.db.users.find_one({"token.token": token}):
            print('token found')
            token = getRandomString(length=48)
        self.user['token']={'token': token, 'created': datetime.datetime.now()}
        mongo.db.users.save(self.user)


    def deleteToken(self):
        self.user['token']={}
        mongo.db.users.save(self.user)


    def setEnabled(self, value):
        self.user['enabled'] = value
        mongo.db.users.save(self.user)


    def setPassword(self, password):
        self.user['password'] = password
        mongo.db.users.save(self.user)


    def toggleEnabled(self):
        if self.user['enabled']:
            self.user['enabled']=False
        else:
            self.user['enabled']=True
        mongo.db.users.save(self.user)
        return self.user['enabled']


    @property
    def admin(self):
        return self.data['admin']


    def toggleAdmin(self):
        if self.admin:
            self.user['admin']=False
        else:
            self.user['admin']=True
        mongo.db.users.save(self.user)
        return self.admin
        

    def setValidatedEmail(self, value):
        self.user['validatedEmail'] = value
        mongo.db.users.save(self.user)
        

    def canViewUser(self, user):
        #if self.username == user.username:
        #    return True
        if self.admin and self.hostname == user.hostname:
            return True
        if self.isRootUser():
            return True
        return False


    def canEditUser(self, user):
        return self.canViewUser(user)


    def canViewForm(self, form):
        if self.username == form.author:
            return True
        if self.admin and self.hostname == form.hostname:
            return True
        if self.isRootUser():
            return True
        return False
    
    
    def canEditForm(self, form):
        if self.username == form.author:
            return True
        return False
        



class Form(object):
    form = None

    def __new__(cls, *args, **kwargs):
        instance = super(Form, cls).__new__(cls)

        if kwargs:
            if g.current_user and not g.current_user.isRootUser():
                # rootUser can find any form. else only find forms created at this hostname.
                kwargs['hostname']=g.hostname
            form = mongo.db.forms.find_one(kwargs)
            if form:
                instance.form=dict(form)
            else:
                return None
        return instance


    def __init__(self, *args, **kwargs):
        pass

    @property
    def data(self):
        return self.form

    @property
    def author(self):
        return self.form['author']

    @property
    def slug(self):
        return self.form['slug']

    @property
    def structure(self):
        return self.form['structure']

    @structure.setter
    def structure(self, value):
        self.form['structure'] = value
    
    @property
    def fieldIndex(self):
        return self.form['fieldIndex']

    """
    @fieldIndex.setter
    def fieldIndex(self, value):
        self.form['fieldIndex'] = value
    """
    
    @property
    def entries(self):
        return self.form['entries']

    @property
    def created(self):
        return self.form['created']


    def findAll(cls, *args, **kwargs):
        if not g.current_user.isRootUser():
            kwargs['hostname']=g.hostname
        if kwargs:
            return mongo.db.forms.find(kwargs)
        return mongo.db.forms.find()


    def toggleEnabled(self):
        if self.form['enabled']:
            self.form['enabled']=False
        else:
            self.form['enabled']=True
        mongo.db.forms.save(self.form)
        return self.form['enabled']

    """
    def canRead(self, username):
        if self.author == username:
            return True
        user=User(username=username)
        if user and user.username == self.author:
            return True
    """

    def insert(self, formData):
        mongo.db.forms.insert_one(formData)

    def update(self, data):
        mongo.db.forms.update_one({'slug':self.slug}, {"$set": data})
    
    def saveEntry(self, entry):
        mongo.db.forms.update({ "_id": self.form["_id"] }, {"$push": {"entries": entry }})

    @property
    def totalEntries(self):
        return len(self.entries)


    @property
    def enabled(self):
        return self.form['enabled']

    @property
    def hostname(self):
        return self.form['hostname']
        

    @property
    def lastEntryDate(self):
        if self.entries:
            last_entry = self.entries[-1] 
            last_entry_date = last_entry["created"]
        else:
            last_entry_date = ""

            
    def isAuthor(self, user):
        if self.author != user.username:
            return False
        return True


    def isAvailable(self):
        if not self.enabled:
            return False
        if not User(username=self.author).enabled:
            return False
        return True



        

class Site(object):
    site = None

    def __new__(cls, *args, **kwargs):
        instance = super(Site, cls).__new__(cls)
        if kwargs:
            site = mongo.db.forms.find_one(kwargs)
            if site:
                instance.site=dict(site)
            else:
                return None
        return instance

    
    def __init__(self, *args, **kwargs):
        pass