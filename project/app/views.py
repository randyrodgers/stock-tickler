from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection 
from .models import * 
import bcrypt
from project.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from pandas_datareader import data
from pandas_datareader._utils import RemoteDataError
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
import time

# Stock Constants
START_DATE = str((datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d'))
END_DATE = str(datetime.now().strftime('%Y-%m-%d'))
ADJ_CLOSE = 'Adj Close'

def index( request ):
    return render( request, 'index.html' )

def add_stock( request ):
    if 'logged_user_id' in request.session:
        context = {
            'user' : User.objects.get( id = request.session['logged_user_id'] )
        }
        return render( request, 'add_stock.html', context )
    return redirect( '/' )

def profile( request ):
    if 'logged_user_id' in request.session:
        context = {
            'user' : User.objects.get( id = request.session['logged_user_id'] ),
            'stocks': User.objects.get( id = request.session['logged_user_id'] ).stocks.all()
        }
        return render( request, 'profile.html', context )
    return redirect( '/' )

def register( request ):
    if request.method == 'POST':
        errors = User.objects.register_validator( request.POST )
        if len( errors ) > 0:
            for value in errors.values():
                messages.error( request, value )
            return redirect( '/' )
        password = request.POST['password'].strip()
        hashed_pw = bcrypt.hashpw( password.encode(), bcrypt.gensalt() ).decode()
        user = User.objects.create( first_name = request.POST['first_name'].strip(),
                                    last_name = request.POST['last_name'].strip(),
                                    email = request.POST['email'].strip().lower(), 
                                    password = hashed_pw )
        request.session['logged_user_id'] = user.id 
        return redirect( '/profile' )
    return redirect( '/' )

def login( request ):
    if request.method == 'POST':
        errors = User.objects.login_validator( request.POST )
        if len( errors ) > 0:
            for value in errors.values():
                messages.error( request, value )
            return redirect( '/' )
        user_list = User.objects.filter( email = request.POST['email'].strip().lower() ) 
        if len( user_list ) > 0:
            logged_user = user_list[0] # email addresses are unique
            if bcrypt.checkpw( request.POST['password'].encode(), logged_user.password.encode() ):
                request.session['logged_user_id'] = logged_user.id 
                return redirect( '/profile' )
    return redirect( '/' )

def logout( request ):
    if 'logged_user_id' in request.session:
        request.session.flush()
    return redirect( '/' )


def update_user_name( request, user_id ):
    if 'logged_user_id' in request.session:
        if request.method == 'POST':
            errors = User.objects.update_name_validator( request.POST )
            if len( errors ) > 0:
                for value in errors.values():
                    messages.error( request, value )
                return redirect( '/profile' )
            user = User.objects.get( id = request.session['logged_user_id'] )
            if bcrypt.checkpw( request.POST['password'].strip().encode(), user.password.encode() ):
                user.first_name = request.POST['first_name'].strip()
                user.last_name = request.POST['last_name'].strip()
                user.save()
        return redirect( '/profile' )
    return redirect( '/' )

def update_user_email( request, user_id ):
    if 'logged_user_id' in request.session:
        if request.method == 'POST':
            errors = User.objects.update_email_validator( request.POST, request.session['logged_user_id'] )
            if len( errors ) > 0:
                for value in errors.values():
                    messages.error( request, value )
                return redirect( '/profile' )
            user = User.objects.get( id = request.session['logged_user_id'] )
            if bcrypt.checkpw( request.POST['password'].strip().encode(), user.password.encode() ):
                user.email = request.POST['email'].strip().lower() 
                user.save()
        return redirect( '/profile' )
    return redirect( '/' )

def udpate_user_password( request, user_id ):
    if 'logged_user_id' in request.session:
        if request.method == 'POST':
            errors = User.objects.update_password_validator( request.POST )
            if len( errors ) > 0:
                for value in errors.values():
                    messages.error( request, value )
                return redirect( '/profile' )
            user = User.objects.get( id = request.session['logged_user_id'] )
            if bcrypt.checkpw( request.POST['password3'].strip().encode(), user.password.encode() ):
                user.password = bcrypt.hashpw( request.POST['password'].strip().encode(), bcrypt.gensalt() ).decode()
                user.save()
        return redirect( '/profile' )
    return redirect( '/' )

def delete_user( request ):
    if 'logged_user_id' in request.session:
        User.objects.get( id = request.session['logged_user_id'] ).delete()
        request.session.flush()
    return redirect( '/' )

def delete_stock( request, stock_id ):
    if 'logged_user_id' in request.session:
        Stock.objects.get( id = stock_id ).delete()
        return redirect( '/profile' )
    return redirect( '/' )

def update_stock_watch_price( request, stock_id):
    if 'logged_user_id' in request.session:
        if request.method == "POST":
            stock = Stock.objects.get( id = stock_id)
            old_price = stock.watch_price
            stock.watch_price = request.POST['watch_price']
            stock.notify = True 
            stock.save()
            subject = "Change to " + stock.ticker + " Watch Price"
            message = "You are receiving this email to confirm that you have changed your watch price for " + stock.ticker + " from $" + str(old_price) + " to $" + str(stock.watch_price) + ". You will now receive an email notification if the stock reaches your new watch price. Thanks for using Stock Tickler!"
            receipient = str(User.objects.get(id = request.session['logged_user_id']).email)
            send_mail(subject, message, EMAIL_HOST_USER, [receipient], fail_silently=False)
        return redirect('/profile')
    return redirect ( '/' )

def find_stock( request ):
    if 'logged_user_id' in request.session:
        if request.method == 'POST':
            errors = Stock.objects.find_stock_validator( request.POST )
            if len( errors ) > 0:
                for value in errors.values():
                    messages.error( request, value )
                return redirect( '/add_stock' )

            stock_data = get_data(request.POST['ticker'], START_DATE, END_DATE)
            cleaned_data = clean_data(stock_data, ADJ_CLOSE, START_DATE, END_DATE)
            stock_stats = get_stats(cleaned_data)
            current_stock_price = stock_stats['last_price']
            
            # Prevent duplicate listings in the Watch List
            user = User.objects.get(id = request.session['logged_user_id'])
            user_ticker_list = []
            for stock in user.stocks.all():
                user_ticker_list.append( stock.ticker )
            if request.POST['ticker'].strip() not in user_ticker_list:
                new_stock = Stock.objects.create(ticker = request.POST['ticker'].strip(), 
                                                current_price = current_stock_price, 
                                                watch_price = request.POST['watch_price'])
                user.stocks.add(new_stock)

            return redirect('/profile')
    return redirect( '/' )

def poll_yahoo_and_alert_if_watch_price_met(request):
    if 'logged_user_id' in request.session:
        master_ticker_list = []

        # populate the master ticker list
        for stock in Stock.objects.all():
            if stock.ticker not in master_ticker_list:
                master_ticker_list.append( stock.ticker )

        # use master ticker list to ...
        for ticker in master_ticker_list:

            # poll yahoo, ...
            stock_data = get_data( ticker, START_DATE, END_DATE )
            cleaned_data = clean_data( stock_data, ADJ_CLOSE, START_DATE, END_DATE )
            stock_stats = get_stats( cleaned_data )
            new_stock_price = Decimal( stock_stats['last_price'] ).quantize( Decimal( '.01' ), rounding = ROUND_DOWN )

            # alert users by ...
            for user in User.objects.all():
                stocks_list = user.stocks.filter( ticker = ticker )
                if len( stocks_list ) > 0:
                    stock = user.stocks.get( ticker = ticker )
                    if stock.notify == True:
                        if new_stock_price >= stock.watch_price and new_stock_price > stock.current_price:
                            # sending an email about the watch price being met
                            subject = "Watch Price for " + stock.ticker + " Met"
                            message = "You are receiving this email, because the current price for " + stock.ticker + ", $" + \
                                    str( new_stock_price ) + ", " + "has met your watch price of $" + str( stock.current_price ) + \
                                    ".\nThanks for using Stock Tickler!"
                            receipient = str( user.email )
                            send_mail( subject, message, EMAIL_HOST_USER, [receipient], fail_silently = False )
                            stock.notify = False 
                            stock.current_price = new_stock_price
                            stock.save()
                        elif new_stock_price <= stock.watch_price and new_stock_price < stock.current_price:
                            # sending an email about the watch price being met
                            subject = "Watch Price for " + stock.ticker + " Met"
                            message = "You are receiving this email, because the current price for " + stock.ticker + ", $" + \
                                    str( new_stock_price ) + ", " + "has met your watch price of $" + str( stock.current_price ) + \
                                    ".\nThanks for using Stock Tickler!"
                            receipient = str( user.email )
                            send_mail( subject, message, EMAIL_HOST_USER, [receipient], fail_silently = False )
                            stock.notify = False 
                            stock.current_price = new_stock_price
                            stock.save()
                    else:
                        stock.current_price = new_stock_price
                        stock.save()

                    # and update the stock
                    # stocks = Stock.objects.filter( ticker = ticker )
                    # for stock in stocks:
                    #     stock.current_price = new_stock_price
                    #     stock.save()
        context = {
            'user' : User.objects.get( id = request.session['logged_user_id'] ),
            'stocks': User.objects.get( id = request.session['logged_user_id'] ).stocks.all()
        }
        return render(request, 'partials/partial_profile.html', context)
    return redirect( '/' )

#################### Helper Methods for Getting Stock ################
def get_data (ticker, start, end):
    return data.DataReader(ticker, 'yahoo', start, end)

def clean_data(stock_data, col, start, end):
    weekdays = pd.date_range(start = start, end = end)
    clean_data = stock_data[col].reindex(weekdays)
    return clean_data.fillna(method = 'ffill')

def get_stats(stock_data):
    return {
        'last_price': np.mean(stock_data.tail(1))
    }

