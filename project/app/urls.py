from django.urls import path
from . import views 

urlpatterns = [
    path( '', views.index ),
    path( 'index', views.index ),
    path( 'add_stock', views.add_stock ),
    path( 'profile', views.profile ),
    path( 'register', views.register ),
    path( 'login', views.login ),
    path( 'logout', views.logout ),
    path( 'update/name/user/<int:user_id>', views.update_user_name ),
    path( 'update/email/user/<int:user_id>', views.update_user_email ),
    path( 'update/password/user/<int:user_id>', views.udpate_user_password ),
    path( 'delete/user', views.delete_user ), 
    path( 'update/stock/watch_price/<int:stock_id>', views.update_stock_watch_price),
    path( 'find_stock', views.find_stock)
]