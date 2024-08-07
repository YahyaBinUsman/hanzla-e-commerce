import datetime
from django.core.mail import send_mail
from django.shortcuts import reverse
from .models import Order

class DeliveryCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()
        orders = Order.objects.filter(delivery_date__lt=today, review_email_sent=False)

        for order in orders:
            review_token = order.review_token
            review_url = request.build_absolute_uri(f'/review/?token={review_token}')
            contact_url = request.build_absolute_uri(reverse('contact'))
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
                'from@example.com',
                [order.email],
                fail_silently=False,
            )
            order.review_email_sent = True
            order.save()

        response = self.get_response(request)
        return response
