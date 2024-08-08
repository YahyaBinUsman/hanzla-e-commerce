import datetime
from decimal import Decimal
from django.core.mail import send_mail
from django.shortcuts import reverse
from django.utils import timezone
from .models import ClientReview, Order
import datetime
from django.core.mail import send_mail
from django.shortcuts import reverse
from django.utils import timezone
from .models import Order

class DeliveryCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()

        # Handle delivery confirmation emails
        orders = Order.objects.filter(delivery_date__lt=today, review_email_sent=False)
        for order in orders:
            review_token = order.review_token
            review_url = request.build_absolute_uri(f'/review/?token={review_token}')
            contact_url = request.build_absolute_uri(reverse('contact', args=[order.id]))
            secret_contact_url = f"{contact_url}?order_id={order.id}&secret=1/"

            email_subject = 'Delivery Confirmation'
            email_body = (
                f'Hello {order.first_name},\n\n'
                f'We hope you have received your order #{order.id}.\n'
                f'If yes, please leave a review here: {review_url}\n'
                f'If no, please contact us here: {secret_contact_url}\n\n'
            )
            send_mail(
                email_subject,
                email_body,
                'yahyabinusman7@gmail.com',
                [order.email],
                fail_silently=False,
            )
            order.review_email_sent = True
            order.save()

        # Handle "not received" emails and repeat the process
        orders_not_received = Order.objects.filter(is_received=False, not_received_clicked=True)
        for order in orders_not_received:
            if timezone.now() >= order.not_received_click_time + datetime.timedelta(days=2):
                # Resend the email asking if the order was received
                contact_url = request.build_absolute_uri(reverse('contact', args=[order.id]))
                send_mail(
                    'Have you received your order?',
                    f'Please click the following link if you have not received your order: {contact_url}',
                    'yahyabinusman7@gmail.com',
                    [order.email],
                    fail_silently=False,
                )

                # Reset the click status to continue the process
                order.not_received_clicked = False
                order.save()

        # Handle auto-review if the review token is expired again
        orders_to_review = Order.objects.filter(reviewed=False, review_token_expiry__lt=timezone.now())
        for order in orders_to_review:
            order.reviewed = True
            order.save()

            # Automatically create a 5-star review with the customer's name
            ClientReview.objects.create(
                name=f"{order.first_name} {order.last_name}",  # Use customer's full name
                description="The order was absolutely great and a fantastic experience.",
                rating=Decimal('5.0')
            )

        response = self.get_response(request)
        return response
