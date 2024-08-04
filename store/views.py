from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.core.mail import send_mail
from datetime import date, timedelta, datetime
from decimal import Decimal
from .models import Product, CartItem, Order, Review
from .forms import CheckoutForm, ReviewForm
from store import models
from django.shortcuts import render
from .models import ClientReview
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.conf import settings

def home(request):
    five_star_reviews = ClientReview.objects.filter(rating=5.0)
    return render(request, 'store/home.html', {'five_star_reviews': five_star_reviews})

def about_us(request):
    return render(request, 'store/about_us.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Construct the email content
        subject = f'New Contact Form Submission from {name}'
        email_message = f'Name: {name}\nPhone Number: {phone_number}\nEmail: {email}\nMessage: {message}'
        recipient_list = ['yahyabinusman7@gmail.com']

        # Send the email
        send_mail(subject, email_message, settings.EMAIL_HOST_USER, recipient_list)

        return redirect('home')  # Redirect to home after successful submission

    return render(request, 'store/contact.html')

# View cart page
def view_cart(request):
    cart_items = CartItem.objects.all()
    cart_items_with_totals = []
    total = Decimal('0.00')

    for item in cart_items:
        item_total = item.product.price * item.quantity
        total += item_total
        cart_items_with_totals.append({
            'item': item,
            'total': item_total
        })

    tax_rate = Decimal('0.17')
    tax = total * tax_rate
    grand_total = total + tax

    return render(request, 'store/view_cart.html', {
        'cart_items_with_totals': cart_items_with_totals,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
    })

# Remove item from cart
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    if item.quantity > 1:
        item.quantity -= 1
        item.product.update_quantity(1)  # Increase product quantity in inventory
        item.save()
    else:
        item.product.update_quantity(item.quantity)  # Increase product quantity in inventory
        item.delete()
    return redirect('view_cart')

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Product, CartItem

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if product.quantity < quantity:
        return redirect('product_list', category=product.category)

    cart_item, created = CartItem.objects.get_or_create(product=product)
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()

    product.update_quantity(-quantity)
    
    # Add success message with product name and quantity
    messages.success(request, f'{quantity} x {product.name} has been added to your cart! Go check your cart.')

    return redirect(request.META.get('HTTP_REFERER', 'home'))



from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.core.mail import send_mail
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Product, CartItem, Order
from .forms import CheckoutForm

# Checkout view
def checkout(request):
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            cart_items = CartItem.objects.all()
            products_info = ', '.join([f"{item.product.name} ({item.quantity})" for item in cart_items])
            order.products = products_info

            subtotal = sum([item.product.price * item.quantity for item in cart_items])
            tax = subtotal * Decimal('0.17')
            total_price = subtotal + tax
            order.total_price = total_price
            order.save()

            for item in cart_items:
                order.cart_items.add(item)

            # Calculate average delivery time
            total_delivery_time = sum(item.product.delivery_time * item.quantity for item in cart_items)
            total_quantity = sum(item.quantity for item in cart_items)
            average_delivery_time = total_delivery_time / total_quantity if total_quantity > 0 else 0

            # Set the delivery date based on average delivery time
            order.delivery_date = datetime.now().date() + timedelta(days=average_delivery_time)
            order.save()

            # Send confirmation email to customer
            email_subject = 'Order Confirmation'
            email_body = (
                f'Thank you for your order!\n\n'
                f'Order details:\n\n'
                f'First Name: {order.first_name}\n'
                f'Last Name: {order.last_name}\n'
                f'Email: {order.email}\n'
                f'Phone: {order.phone}\n'
                f'Address: {order.address}\n'
                f'City: {order.city}\n'
                f'Postal Code: {order.postal_code}\n'
                f'Payment Method: {order.payment_method}\n'
                f'Country: {order.country}\n'
                f'Order Date: {order.order_date}\n'
                f'Delivery Date: {order.delivery_date}\n'
                f'Subtotal: ${subtotal}\n'
                f'Tax (17%): ${tax}\n'
                f'Total Price (After Tax): ${order.total_price}\n\n'
                f'Products:\n{order.products}\n\n'
                f'Your order has been received. Please expect a delivery confirmation email soon.'
            )
            send_mail(
                email_subject,
                email_body,
                'from@example.com',
                [order.email],
                fail_silently=False,
            )

            # Send email to admin
            admin_email_subject = 'A new order has been placed'
            admin_email_body = (
                f'Order details:\n\n'
                f'First Name: {order.first_name}\n'
                f'Last Name: {order.last_name}\n'
                f'Email: {order.email}\n'
                f'Phone: {order.phone}\n'
                f'Address: {order.address}\n'
                f'City: {order.city}\n'
                f'Postal Code: {order.postal_code}\n'
                f'Payment Method: {order.payment_method}\n'
                f'Country: {order.country}\n'
                f'Order Date: {order.order_date}\n'
                f'Delivery Date: {order.delivery_date}\n'
                f'Subtotal: ${subtotal}\n'
                f'Tax (17%): ${tax}\n'
                f'Total Price (After Tax): ${order.total_price}\n\n'
                f'Products:\n{order.products}\n\n'
            )
            send_mail(
                admin_email_subject,
                admin_email_body,
                'from@example.com',
                ['yahyabinusman7@gmail.com'],
                fail_silently=False,
            )

            cart_items.delete()
            return redirect('order_confirmation')
    else:
        form = CheckoutForm(initial={'payment_method': 'Cash on Delivery', 'country': 'Pakistan'})

    return render(request, 'store/checkout.html', {'form': form})

from django.http import JsonResponse
from datetime import date
from django.core.mail import send_mail
from .models import Order

def check_delivery_dates(request):
    today = date.today()
    orders = Order.objects.filter(delivery_date__lt=today, review_email_sent=False)

    email_sent = False
    for order in orders:
        order.review_email_sent = True
        order.save()
        email_sent = True

    return JsonResponse({'email_sent': email_sent})

def order_confirmation(request):
    return render(request, 'store/order_confirmation.html')

# Order details page for admin
def order_details(request):
    orders = Order.objects.all()
    return render(request, 'store/order_details.html', {'orders': orders})
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from decimal import Decimal
from .models import Product, Review, ClientReview, Order

def review_page(request):
    token = request.GET.get('token')

    if not token:
        return HttpResponseBadRequest("Token is missing")

    try:
        order = Order.objects.get(review_token=token)
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Invalid token")

    if order.reviewed:
        return render(request, 'store/review_submitted.html')  # A page indicating review is already submitted.

    product_names = [item.split(' (')[0] for item in order.products.split(', ')]
    products = Product.objects.filter(name__in=product_names)

    if request.method == 'POST':
        overall_rating = request.POST.get('overall_rating')
        overall_name = request.POST.get('overall_name')
        overall_description = request.POST.get('overall_description')

        if not overall_rating or not overall_name or not overall_description:
            return HttpResponseBadRequest("All fields are required")

        overall_rating = Decimal(overall_rating)
        total_product_ratings = 0
        count_product_ratings = 0

        for product in products:
            rating = request.POST.get(f'rating_{product.id}')
            description = request.POST.get(f'description_{product.id}')
            if rating and description:
                review = Review(product=product, name=overall_name, description=description, rating=Decimal(rating))
                review.save()
                product.update_average_rating()
                total_product_ratings += Decimal(rating)
                count_product_ratings += 1

        average_product_rating = (total_product_ratings / count_product_ratings) if count_product_ratings else 0
        combined_rating = (average_product_rating + overall_rating) / 2 if count_product_ratings else overall_rating

        ClientReview.objects.create(name=overall_name, description=overall_description, rating=combined_rating)

        order.reviewed = True
        order.save()

        return redirect('home')

    return render(request, 'store/review_page.html', {
        'products': products,
        'product_ratings_average': 0,  # Not displaying this because it's for the current user's input
        'combined_rating': 0  # Not displaying this because it's for the current user's input
    })

from django.shortcuts import render
from .models import ClientReview
from django.shortcuts import render
from .models import ClientReview
from django.shortcuts import render
from .models import ClientReview

def testimonials(request):
    reviews = ClientReview.objects.all()
    
    # Round the ratings to the nearest 0.5
    for review in reviews:
        review.rating = round(review.rating * 2) / 2
    
    if reviews:
        combined_average_rating = sum(review.rating for review in reviews) / len(reviews)
    else:
        combined_average_rating = 0

    return render(request, 'store/testimonials.html', {
        'reviews': reviews,
        'combined_average_rating': combined_average_rating
    })


from django.db.models import Count, Q
from .models import Product

def product_list(request, category):
    # Annotate each product with the count of 5-star reviews
    products = Product.objects.filter(category=category).annotate(
        five_star_review_count=Count('reviews', filter=Q(reviews__rating=5))
    )
    return render(request, 'store/product_list.html', {'products': products, 'category': category})
