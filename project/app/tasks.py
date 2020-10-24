from celery.decorators import periodic_task, task
from django.core.mail import send_mail
from pandas_datareader import data
from pandas_datareader._utils import RemoteDataError
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from project.settings import EMAIL_HOST_USER
from .models import *

# Stock Constants
START_DATE = str((datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d'))
END_DATE = str(datetime.now().strftime('%Y-%m-%d'))
ADJ_CLOSE = 'Adj Close'

@task
def send_watch_price_changed_email( ticker, old_price, watch_price, user_email ):
    subject = "Change to " + stock.ticker + " Watch Price"
    message = "You are receiving this email to confirm that you have changed your watch price for " + \
              stock.ticker + " from $" + str(old_price) + " to $" + str(stock.watch_price) + \
              ". You will now receive an email notification if the stock reaches your new watch price." + \
              "Thanks for using Stock Tickler!"
    send_mail( subject, message, EMAIL_HOST_USER, [user_email], fail_silently = False )

@task
def send_watch_price_alert_email( ticker, current_price, new_price, user_email ):
    subject = "Watch Price for " + ticker + " Met"
    message = "You are receiving this email, because the current price for " + ticker + ", $" + \
              str( new_price ) + ", " + "has met your watch price of $" + str( current_price ) + \
              ".\nThanks for using Stock Tickler!"
    receipient = str( user_email )
    send_mail( subject, message, EMAIL_HOST_USER, [receipient], fail_silently = False )

@periodic_task
def poll_yahoo_and_alert_if_watch_price_met( run_every = timedelta( minutes = 15 ) ):
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
        new_stock_price = stock_stats['last_price']

        # alert users by ...
        for user in User.objects.all():
            stocks_list = user.stocks.filter( ticker = ticker )
            if len( stocks_list ) > 0:
                stock = user.stocks.get( ticker = ticker )
                if stock.notify == True:
                    # case: the new price has traced upwards from the current price, past or equal to the watch price 
                    if new_stock_price >= stock.watch_price and new_stock_price > stock.current_price and stock.watch_price > stock.current_price:
                        # ... sending an email about the watch price being met ...
                        send_watch_price_alert_email( ticker = stock.ticker, 
                                                      current_price = stock.current_price, 
                                                      new_price = new_stock_price, 
                                                      user_email = user.email )
                        # ... and updating the stock
                        stock.notify = False 
                        stock.current_price = new_stock_price
                        stock.save()
                    # case: the new price has traced downwards from the current price, past or equal to the watch price
                    elif new_stock_price <= stock.watch_price and new_stock_price < stock.current_price and stock.watch_price < stock.current_price:
                        # ... sending an email about the watch price being met ...
                        send_watch_price_alert_email( ticker = stock.ticker, 
                                                      current_price = stock.current_price, 
                                                      new_price = new_stock_price, 
                                                      user_email = user.email )
                        # ... and updating the stock
                        stock.notify = False 
                        stock.current_price = new_stock_price
                        stock.save()
                else:
                    stock.current_price = new_stock_price
                    stock.save()

#################### Helper Methods for Getting Stock ################
@task
def get_data (ticker, start, end):
    return data.DataReader(ticker, 'yahoo', start, end)

@task
def clean_data(stock_data, col, start, end):
    weekdays = pd.date_range(start = start, end = end)
    clean_data = stock_data[col].reindex(weekdays)
    return clean_data.fillna(method = 'ffill')

@task
def get_stats(stock_data):
    return {
        'last_price': np.mean(stock_data.tail(1))
    }
