from django.core.mail import send_mail
from pandas_datareader import data
from pandas_datareader._utils import RemoteDataError
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from project.settings import EMAIL_HOST_USER
from .models import *
from celery import current_app
app = current_app._get_current_object()

# Stock Constants
START_DATE = str((datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d'))
END_DATE = str(datetime.now().strftime('%Y-%m-%d'))
ADJ_CLOSE = 'Adj Close'

@app.task
def send_watch_price_changed_email( ticker, old_price, watch_price, user_email ):
    subject = "Change to " + ticker + " Watch Price"
    message = "You are receiving this email to confirm that you have changed your watch price for " + \
              ticker + " from $" + old_price + " to $" + watch_price + \
              ". You will now receive an email notification if the stock reaches your new watch price. " + \
              "Thanks for using Stock Tickler!"
    send_mail( subject, message, EMAIL_HOST_USER, [user_email], fail_silently = False )

@app.task
def send_watch_price_met_email( ticker, current_price, new_price, user_email ):
    subject = "Watch Price for " + ticker + " Met"
    message = "You are receiving this email, because the current price for " + ticker + ", $" + \
              str( new_price ) + ", " + "has met your watch price of $" + str( current_price ) + \
              ".\nThanks for using Stock Tickler!"
    receipient = str( user_email )
    send_mail( subject, message, EMAIL_HOST_USER, [receipient], fail_silently = False )

@app.task
def poll_yahoo_and_alert_if_watch_price_met():
    master_ticker_list = []

    # populate the master ticker list
    for stock in Stock.objects.all():
        if stock.ticker not in master_ticker_list:
            master_ticker_list.append( stock.ticker )

    # use master ticker list to ...
    for ticker in master_ticker_list:

        # poll yahoo, ...
        new_stock_price = get_stock_price( ticker = ticker, start = START_DATE, end = END_DATE )

        # alert users by ...
        for user in User.objects.all():
            stocks_list = user.stocks.filter( ticker = ticker )
            if len( stocks_list ) > 0:
                stock = user.stocks.get( ticker = ticker )
                if stock.notify == True:
                    # case: the new price has traced upwards from the current price, past or equal to the watch price 
                    if new_stock_price >= stock.watch_price and new_stock_price > stock.current_price and stock.watch_price > stock.current_price:
                        # ... sending an email about the watch price being met ...
                        send_watch_price_met_email( ticker = stock.ticker, 
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
                        send_watch_price_met_email( ticker = stock.ticker, 
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

@app.task
def get_stock_price( ticker, start, end ):
    stock_data = data.DataReader( ticker, 'yahoo', start, end )
    weekdays = pd.date_range( start = start, end = end )
    clean_data = stock_data[ ADJ_CLOSE ].reindex( weekdays )
    cleaned_data = clean_data.fillna( method = 'ffill' )
    return np.mean( cleaned_data.tail( 1 ) ) # stock's last price

##################### Add Periodic Tasks ###################
@app.on_after_finalize.connect
def app_ready( **kwargs ):
    '''
    Called once after app has been finalized.
    '''
    sender = kwargs.get( 'sender' )

    # periodic tasks
    interval = 900 # 900 seconds == 15 minutes
    sender.add_periodic_task( interval, poll_yahoo_and_alert_if_watch_price_met.s() )
