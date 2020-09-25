from django.db import models
import re

######################## Managers ########################

class StockManager( models.Manager ):
    pass

class UserManager( models.Manager ):
    def register_validator( self, form ):
        errors = {}
        EMAIL_REGEX = re.compile( r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$' )
        if form['first_name'] == '':
            errors['first_name'] = 'First name must be provided.'
        if form['last_name'] == '':
            errors['last_name'] = 'Last name must be provided.'
        if not EMAIL_REGEX.match( form['email'] ):
            errors['email_invalid'] = 'Email must be in a valid format.'
        if User.objects.filter( email = form['email'] ):
            errors['email_exists'] = "Email address is already registered."
        if form['password'] != form['password2']:
            errors['password_mismatch'] = "Check that your password confirmation matches the supplied password."
        if len( form['password'] ) < 8:
            errors['password_length'] = 'Password must be at least 8 characters.'
        return errors

    def login_validator( self, form ):
        errors = {}
        EMAIL_REGEX = re.compile( r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$' )
        if not EMAIL_REGEX.match( form['email'] ):
            errors['email_invalid'] = 'Email must be in a valid format.'
        if len( form['password'] ) < 8:
            errors['password_length'] = 'Password must be at least 8 characters.'
        return errors

######################## Models #########################

class Stock( models.Model ):
    ticker = models.CharField( max_length = 10 )
    watch_price = models.DecimalField( max_digits = 11, decimal_places = 2 )
    created_at = models.DateTimeField( auto_now_add = True )
    updated_at = models.DateTimeField( auto_now = True )
    # objects = StockManager()

class User( models.Model ):
    first_name = models.CharField( max_length = 100 )
    last_name = models.CharField( max_length = 100 )
    email = models.EmailField( max_length = 100, unique = True )
    password = models.CharField( max_length = 100 )
    stocks = models.ManyToManyField( Stock, related_name = "watchers" )
    created_at = models.DateTimeField( auto_now_add = True )
    updated_at = models.DateTimeField( auto_now = True )
    objects = UserManager()
