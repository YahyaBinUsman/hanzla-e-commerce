import datetime
from django.core.mail import send_mail
from .models import Order

class DeliveryCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = datetime.date.today()
        orders = Order.objects.filter(delivery_date__lt=today, review_email_sent=False)

        for order in orders:
            email_subject = 'Delivery Confirmation'
            review_url = request.build_absolute_uri('/review/')
            home_url = request.build_absolute_uri('/')
            email_body = (
                f'Hello {order.first_name},\n\n'
                f'We hope you have received your order #{order.id}.\n'
                f'If yes, please leave a review here: {review_url}\n'
                f'If no, please contact us: {home_url}'
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
