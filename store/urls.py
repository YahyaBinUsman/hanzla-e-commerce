from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<str:category>/', views.product_list, name='product_list'),
    path('cart/', views.view_cart, name='view_cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order_comfirmation', views.order_confirmation, name='order_confirmation'),
    path('order_details/', views.order_details, name='order_details'),
    path('review/', views.review_page, name='review_page'),
    path('check_delivery_dates/', views.check_delivery_dates, name='check_delivery_dates'),




]
