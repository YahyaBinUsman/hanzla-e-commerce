from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order,ClientReview
from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal

@receiver(post_save, sender=Order)
def auto_rate_order(sender, instance, created, **kwargs):
    if created:
        instance.review_token_expiry = timezone.now() + timedelta(days=3)
        instance.save()
    else:
        if not instance.reviewed and timezone.now() > instance.review_token_expiry:
            instance.reviewed = True
            instance.save()

            # Automatically create a 5-star review with the customer's name
            ClientReview.objects.create(
                name=instance.first_name + ' ' + instance.last_name,  # Use customer's full name
                description="The order was absolutely great and a fantastic experience.",
                rating=Decimal('5.0')
            )

