from django.urls import path
from . import views 

urlpatterns = [
    path( '', views.index ),
    path( 'index', views.index ),
    path( 'success', views.success ),
    path( 'profile', views.profile ),
    path( 'register', views.register ),
    path( 'login', views.login ),
    path( 'logout', views.logout ),
]