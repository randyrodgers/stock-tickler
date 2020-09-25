from django.shortcuts import render, redirect
from django.contrib import messages
from .models import * 
import bcrypt 

def index( request ):
    return render( request, 'index.html' )

def success( request ):
    context = {}
    return render( request, 'success.html', context )

def profile( request ):
    context = {}
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
