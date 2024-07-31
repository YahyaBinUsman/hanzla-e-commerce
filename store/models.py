from django.db import models
from datetime import timedelta
from django.db import models
from datetime import timedelta
from django.utils import timezone

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
from django.db import models
from datetime import timedelta
from django.db import models
from datetime import timedelta
from django.db import models
from datetime import timedelta
import uuid

from django.utils import timezone
import uuid

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

    def __str__(self):
        return f"Order {self.id} by {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField()

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)