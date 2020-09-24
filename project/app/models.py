from django.db import models
import re

######################## Managers ########################

class StockManager( models.Manager ):
    pass

class UserManager( models.Manager ):
    def login_validator( self, form ):
        pass
    def register_validator( self, form ):
        pass 

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
    # objects = UserManager()
