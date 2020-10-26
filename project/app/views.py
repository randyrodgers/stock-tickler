from django.shortcuts import render, redirect
from django.contrib import messages
from .models import * 
import bcrypt
from .tasks import send_watch_price_changed_email, \
                   START_DATE, \
                   END_DATE, \
                   ADJ_CLOSE, \
                   get_stock_price

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

def update_stock_watch_price( request, stock_id ):
    if 'logged_user_id' in request.session:
        if request.method == "POST":
            # update watch price
            stock = Stock.objects.get( id = stock_id)
            old_price = stock.watch_price
            stock.watch_price = request.POST['watch_price']
            stock.save()
            # send e-mail alert
            recipient = User.objects.get( id = request.session['logged_user_id']).email 
            send_watch_price_changed_email.delay( ticker = stock.ticker, 
                                            old_price = str( old_price ), 
                                            watch_price = str( stock.watch_price ), 
                                            user_email = str( recipient ) )
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

            current_stock_price = get_stock_price( ticker = request.POST['ticker'], start = START_DATE, end = END_DATE )

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
