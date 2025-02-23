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
    path('testimonials/', views.testimonials, name='testimonials'),
    path('contact1/', views.contact1, name='contact1'),
    path('about/', views.about_us, name='about_us'),
    path('report_non_delivery/', views.report_non_delivery, name='report_non_delivery'),
    path('manage_products/',  views.manage_products, name='manage_products'),
    path('add_product/',  views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/',  views.edit_product, name='edit_product'),
    path('contact/<int:order_id>/', views.contact, name='contact'),

]

