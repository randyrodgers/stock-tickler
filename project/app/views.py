from django.shortcuts import render, redirect, HttpResponse

def index( request ):
    return render( request, 'index.html' )

def success( request ):
    context = {}
    return render( request, 'success.html', context )

def profile( request ):
    context = {}
    return render( request, 'profile.html', context )
