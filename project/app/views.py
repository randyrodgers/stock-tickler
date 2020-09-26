from django.shortcuts import render, redirect
from django.contrib import messages
from .models import * 
import bcrypt 
from project.settings import EMAIL_HOST_USER
from django.core.mail import send_mail

def index( request ):
    return render( request, 'index.html' )

def success( request ):
    if 'logged_user_id' in request.session:
        context = {
            'user' : User.objects.get( id = request.session['logged_user_id'] )
        }
        return render( request, 'success.html', context )
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
                                    email = request.POST['email'].strip(),
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
        user_list = User.objects.filter( email = request.POST['email'] )
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
                user.email = request.POST['email'].strip()
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

def update_stock_watch_price( request, stock_id):
    if request.method == "POST":
        stock = Stock.objects.get( id = stock_id)
        old_price = stock.watch_price
        stock.watch_price = request.POST['id_watch_price']
        stock.save()
        subject = "Change to " + stock.ticker + " Watch Price"
        message = "You are receiving this email to confirm that you have changed your watch price for " + stock.ticker + " from $" + str(old_price) + " to $" + str(stock.watch_price) + ". You will now receive an email notification if the stock reaches your new watch price. Thanks for using Stock Tickler!"
        receipient = str(User.objects.get(id = request.session['logged_user_id']).email)
        send_mail(subject, message, EMAIL_HOST_USER, [receipient], fail_silently=False)
    return redirect('/profile')
