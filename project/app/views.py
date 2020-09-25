from django.shortcuts import render, redirect
from django.contrib import messages
from .models import * 
import bcrypt 

def index( request ):
    return render( request, 'index.html' )

def success( request ):
    context = {
        'user' : User.objects.get( id = request.session['logged_user_id'] )
    }
    return render( request, 'success.html', context )

def profile( request ):
    context = {
        'user' : User.objects.get( id = request.session['logged_user_id'] )
    }
    return render( request, 'profile.html', context )

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
    request.session.flush()
    return redirect( '/' )

def update_user_name( request, user_id ):
    if request.method == 'POST':
        errors = User.objects.update_name_validator( request.POST )
        if len( errors ) > 0:
            print( 'Errors detected:')
            for value in errors.values():
                print( f'{value}')
                messages.error( request, value )
            print( 'Returning to profile.html')
            return redirect( '/profile' )
        user = User.objects.get( id = request.session['logged_user_id'] )
        if bcrypt.checkpw( request.POST['password'].strip().encode(), user.password.encode() ):
            user.first_name = request.POST['first_name'].strip()
            user.last_name = request.POST['last_name'].strip()
            user.save()
    return redirect( '/profile' )

def update_user_email( request, user_id ):
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

def udpate_user_password( request, user_id ):
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

def delete_user( request ):
    User.objects.get( id = request.session['logged_user_id'] ).delete()
    request.session.flush()
    return redirect( '/' )
