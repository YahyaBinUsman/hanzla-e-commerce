from django.contrib import admin
from .models import Product, CartItem, CheckoutInfo, Order

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'quantity', 'delivery_time')

admin.site.register(Product, ProductAdmin)
admin.site.register(CartItem)
admin.site.register(CheckoutInfo)
admin.site.register(Order)
