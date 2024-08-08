from django.db import models
from datetime import timedelta
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.db import models
from datetime import timedelta
from django.db import models
from datetime import timedelta
from django.db import models
from datetime import timedelta
import uuid
# models.py
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
import uuid
from datetime import date

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('towel', 'Towel'),
        ('bedsheet', 'Bed Sheet'),
        ('ahram', 'Ahram'),
        ('slipper', 'Slipper'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    delivery_time = models.PositiveIntegerField(help_text="Delivery time in days")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def update_average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.save()

    def update_quantity(self, quantity_change):
        self.quantity = models.F('quantity') + quantity_change
        self.save(update_fields=['quantity'])

    def __str__(self):
        return self.name

    def expected_delivery_date(self):
        return self.order_date + timedelta(days=self.delivery_time)


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} of {self.product.name}'

class CheckoutInfo(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    address = models.TextField()
    cart_items = models.ManyToManyField(CartItem)

    def __str__(self):
        return self.name

class Order(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    country = models.CharField(max_length=50, default='Pakistan')
    order_date = models.DateTimeField(auto_now_add=True)
    products = models.TextField()
    delivery_date = models.DateField(null=True, blank=True)
    cart_items = models.ManyToManyField(CartItem)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    review_token = models.UUIDField(default=uuid.uuid4)
    review_email_sent = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)
    not_received_clicked = models.BooleanField(default=False)
    not_received_click_time = models.DateTimeField(null=True, blank=True)
    review_token_expiry = models.DateTimeField(default=timezone.now() + timedelta(days=30))

    is_received = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} by {self.first_name} {self.last_name}"


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class ClientReview(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField()

class CityDeliveryInfo(models.Model):
    city = models.CharField(max_length=100)
    delivery_days = models.PositiveIntegerField()
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.city

    @staticmethod
    def populate_cities():
        cities = [
            {'city': 'Lahore', 'delivery_days': 1, 'delivery_charge': 100},
            {'city': 'Karachi', 'delivery_days': 7, 'delivery_charge': 500},
            {'city': 'Islamabad', 'delivery_days': 1, 'delivery_charge': 150},
            {'city': 'Faisalabad', 'delivery_days': 1, 'delivery_charge': 120},
            {'city': 'Rawalpindi', 'delivery_days': 1, 'delivery_charge': 130},
            {'city': 'Multan', 'delivery_days': 2, 'delivery_charge': 180},
            {'city': 'Gujranwala', 'delivery_days': 1, 'delivery_charge': 110},
            {'city': 'Peshawar', 'delivery_days': 2, 'delivery_charge': 200},
            {'city': 'Quetta', 'delivery_days': 3, 'delivery_charge': 250},
            {'city': 'Sialkot', 'delivery_days': 1, 'delivery_charge': 120},
            {'city': 'Bahawalpur', 'delivery_days': 2, 'delivery_charge': 160},
            {'city': 'Sargodha', 'delivery_days': 2, 'delivery_charge': 140},
            {'city': 'Sukkur', 'delivery_days': 3, 'delivery_charge': 220},
            {'city': 'Larkana', 'delivery_days': 3, 'delivery_charge': 210},
            {'city': 'Sheikhupura', 'delivery_days': 1, 'delivery_charge': 110},
            {'city': 'Mardan', 'delivery_days': 2, 'delivery_charge': 170},
            {'city': 'Gujrat', 'delivery_days': 1, 'delivery_charge': 120},
            {'city': 'Rahim Yar Khan', 'delivery_days': 2, 'delivery_charge': 180},
            {'city': 'Kasur', 'delivery_days': 1, 'delivery_charge': 100},
            {'city': 'Sahiwal', 'delivery_days': 2, 'delivery_charge': 150},
            {'city': 'Okara', 'delivery_days': 2, 'delivery_charge': 140},
            {'city': 'Wah Cantonment', 'delivery_days': 1, 'delivery_charge': 130},
            {'city': 'Dera Ghazi Khan', 'delivery_days': 3, 'delivery_charge': 220},
            {'city': 'Mingora', 'delivery_days': 3, 'delivery_charge': 230},
            {'city': 'Nawabshah', 'delivery_days': 3, 'delivery_charge': 210},
            {'city': 'Chiniot', 'delivery_days': 1, 'delivery_charge': 120},
            {'city': 'Jhelum', 'delivery_days': 2, 'delivery_charge': 150},
            {'city': 'Sadiqabad', 'delivery_days': 2, 'delivery_charge': 170},
            {'city': 'Jacobabad', 'delivery_days': 3, 'delivery_charge': 240},
            {'city': 'Shikarpur', 'delivery_days': 3, 'delivery_charge': 230},
            {'city': 'Khanewal', 'delivery_days': 2, 'delivery_charge': 160},
            {'city': 'Hafizabad', 'delivery_days': 1, 'delivery_charge': 110},
            {'city': 'Kohat', 'delivery_days': 3, 'delivery_charge': 210},
            {'city': 'Daska', 'delivery_days': 1, 'delivery_charge': 100},
            {'city': 'Muridke', 'delivery_days': 1, 'delivery_charge': 100},
            {'city': 'Bannu', 'delivery_days': 3, 'delivery_charge': 220},
            {'city': 'Hangu', 'delivery_days': 3, 'delivery_charge': 230},
            {'city': 'Kotli', 'delivery_days': 5, 'delivery_charge': 800},
            {'city': 'Muzaffarabad', 'delivery_days': 3, 'delivery_charge': 240},
        ]

        for city in cities:
            CityDeliveryInfo.objects.get_or_create(**city)

@receiver(post_migrate)
def populate_city_delivery_info(sender, **kwargs):
    if sender.name == 'store':  # Replace 'store' with your actual app name
        CityDeliveryInfo.populate_cities()

class DailyDiscountCode(models.Model):
    code = models.CharField(max_length=8)
    date = models.DateField(default=date.today)
    used_by = models.ManyToManyField('auth.User', related_name='used_discount_codes', blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.date}"
