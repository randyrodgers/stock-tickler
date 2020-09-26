from django.db import models
import re
from pandas_datareader import data
from pandas_datareader._utils import RemoteDataError
import pandas as pd
import numpy as np
from datetime import datetime

######################## Managers ########################

class StockManager( models.Manager ):
    def find_stock_validator(self, form):
        errors = {}
        START_DATE = '2005-01-01'
        END_DATE = str(datetime.now().strftime('%Y-%m-%d'))
        try: 
            stock_data = data.DataReader(form['ticker'], 'yahoo', START_DATE, END_DATE)
        except RemoteDataError:
            errors['ticker'] = 'No stock data found for ' + form['ticker'] + '!'
        return errors

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

    def update_name_validator( self, form ):
        errors = {}
        if form['first_name'] == '':
            errors['first_name'] = 'First name must be provided.'
        if form['last_name'] == '':
            errors['last_name'] = 'Last name must be provided.'
        if form['password'] == '':
            errors['password'] = 'Password must be provided.'
        return errors
    
    def update_email_validator( self, form, user_id ):
        errors = {}
        EMAIL_REGEX = re.compile( r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$' )
        if not EMAIL_REGEX.match( form['email'] ):
            errors['email_invalid'] = 'Email must be in a valid email format.'
        if User.objects.filter( email = form['email'].strip() ):
            if form['email'].strip() != User.objects.get( id = user_id ).email:
                errors['email_exists'] = 'Email is already in use.'
        if form['password'] == '':
            errors['password'] = 'Password must be provided.'
        return errors
    
    def update_password_validator( self, form ):
        errors = {}
        if form['password'] != form['password2']:
            errors['password_mismatch'] = 'Check that your password confirmation matches your new password.'
        if len( form['password'] ) < 8:
            errors['password_length'] = 'New password must be at least 8 characters.'
        if len( form['password3'] ) < 1:
            errors['password_needed'] = 'Old password required.'
        return errors

######################## Models #########################

class Stock( models.Model ):
    ticker = models.CharField( max_length = 10 )
    current_price = models.DecimalField( max_digits = 11, decimal_places = 2 )
    watch_price = models.DecimalField( max_digits = 11, decimal_places = 2 )
    created_at = models.DateTimeField( auto_now_add = True )
    updated_at = models.DateTimeField( auto_now = True )
    objects = StockManager()

class User( models.Model ):
    first_name = models.CharField( max_length = 100 )
    last_name = models.CharField( max_length = 100 )
    email = models.EmailField( max_length = 100, unique = True )
    password = models.CharField( max_length = 100 )
    stocks = models.ManyToManyField( Stock, related_name = "watchers" )
    created_at = models.DateTimeField( auto_now_add = True )
    updated_at = models.DateTimeField( auto_now = True )
    objects = UserManager()
