from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.core.mail import send_mail
from datetime import date, timedelta, datetime
from django.utils import timezone

from decimal import Decimal
from .models import CityDeliveryInfo, Product, CartItem, Order, Review
from .forms import CheckoutForm, ReviewForm
from store import models
from django.shortcuts import render
from .models import ClientReview
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F

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

    elif request.GET.get('secret') == '1':
        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        
        admin_email_subject = 'Order Not Received Notification'
        admin_email_body = (
            f'The following order has been reported as not received:\n\n'
            f'Order ID: {order.id}\n'
            f'Customer Name: {order.first_name} {order.last_name}\n'
            f'Email: {order.email}\n'
            f'Phone: {order.phone}\n'
            f'Address: {order.address}\n'
            f'City: {order.city}\n'
            f'Postal Code: {order.postal_code}\n'
            f'Delivery Date: {order.delivery_date}\n'
        )
        send_mail(
            admin_email_subject,
            admin_email_body,
            settings.EMAIL_HOST_USER,
            ['yahyabinusman7@gmail.com'],
            fail_silently=False,
        )

    return render(request, 'store/home.html')

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
from django.urls import reverse
def checkout(request):
    generate_daily_discount_code()  # Generate and email the code

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            discount_code = request.POST.get('discount_code', '')
            today_code = DailyDiscountCode.objects.filter(date=date.today(), code=discount_code).first()
            permanent_code = '2pd93al8'
            discount = Decimal('0.00')
            discount_applied = False

            if discount_code and discount_code != permanent_code:
                if not today_code:
                    return HttpResponseBadRequest('Invalid discount code')

                if request.user in today_code.used_by.all():
                    return HttpResponseBadRequest('You have already used today\'s discount code')
                today_code.used_by.add(request.user)
                today_code.save()
                discount = Decimal('0.10')
                discount_applied = True
            elif discount_code == permanent_code:
                discount = Decimal('0.10')
                discount_applied = True

            order = form.save(commit=False)
            cart_items = CartItem.objects.all()
            products_info = ', '.join([f"{item.product.name} ({item.quantity})" for item in cart_items])
            order.products = products_info

            subtotal = sum([item.product.price * item.quantity for item in cart_items])
            discount_amount = subtotal * discount
            subtotal -= discount_amount
            tax = subtotal * Decimal('0.17')
            total_price = subtotal + tax

            # Calculate delivery charges based on the city and quantity
            city = form.cleaned_data['city']
            city_info = CityDeliveryInfo.objects.get(city=city)
            delivery_charge = city_info.delivery_charge
            total_quantity = sum(item.quantity for item in cart_items)

            # Adjust delivery charge based on quantity
            if total_quantity > 30:
                delivery_charge *= Decimal('3.00')  # 200% more
            elif total_quantity > 15:
                delivery_charge *= Decimal('2.00')  # 100% more

            total_price += delivery_charge

            # Set the delivery date based on city delivery days
            delivery_days = city_info.delivery_days
            order.delivery_date = timezone.now().date() + timedelta(days=delivery_days)
            order.total_price = total_price
            order.save()

            for item in cart_items:
                order.cart_items.add(item)

            order.user = request.user
            order.save()

            # Prepare the discount message
            discount_message = ''
            if discount_applied:
                discount_message = f'A discount of 10% has been applied to your order.\n\n'

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
                f'Subtotal: Rs {subtotal}\n'
                f'Tax (17%): Rs {tax}\n'
                f'Delivery Charge: Rs {delivery_charge}\n'
                f'Total Price (After Tax): Rs {order.total_price}\n\n'
                f'Products:\n{order.products}\n\n'
                f'{discount_message}'
                f'Your order has been received. Please expect a delivery confirmation email soon.'
            )
            send_mail(
                email_subject,
                email_body,
                settings.EMAIL_HOST_USER,
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
                f'Subtotal: Rs {subtotal}\n'
                f'Tax (17%): Rs {tax}\n'
                f'Delivery Charge: Rs {delivery_charge}\n'
                f'Total Price (After Tax): Rs {order.total_price}\n\n'
                f'Products:\n{order.products}\n\n'
                f'{discount_message}'
            )
            send_mail(
                admin_email_subject,
                admin_email_body,
                settings.EMAIL_HOST_USER,
                ['yahyabinusman7@gmail.com'],
                fail_silently=False,
            )

            cart_items.delete()
            return redirect('order_confirmation')
    else:
        form = CheckoutForm(initial={'payment_method': 'Cash on Delivery', 'country': 'Pakistan'})

    return render(request, 'store/checkout.html', {'form': form})


from django.views.decorators.http import require_GET

@require_GET
def report_non_delivery(request):
    order_id = request.GET.get('order_id')
    if not order_id:
        return HttpResponseBadRequest("Order ID is missing")

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Invalid order ID")

    # Send email to admin about the non-delivery
    email_subject = 'Non-delivery Report'
    email_body = (
        f'The following order has been reported as not received:\n\n'
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
        f'Products:\n{order.products}\n'
    )
    send_mail(
        email_subject,
        email_body,
        settings.EMAIL_HOST_USER,
        ['yahyabinusman7@gmail.com'],
        fail_silently=False,
    )

    return redirect('contact')

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

@staff_member_required
def order_details(request):
    # Filter orders to show only those that have not been reviewed
    pending_orders = Order.objects.filter(reviewed=False)

    # Calculate total sales for reviewed orders
    total_sales = Order.objects.filter(reviewed=True).aggregate(total_sales=Sum('total_price'))['total_sales'] or 0

    return render(request, 'store/order_details.html', {
        'orders': pending_orders,
        'total_sales': total_sales
    })


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

import random
import string
from datetime import date
from django.core.mail import send_mail
from django.conf import settings
from .models import DailyDiscountCode

def generate_daily_discount_code():
    today = date.today()
    existing_code = DailyDiscountCode.objects.filter(date=today).first()
    
    if not existing_code:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        new_code = DailyDiscountCode.objects.create(code=code)
        
        # Send the code via email
        send_mail(
            'Your Daily Discount Code',
            f'Today\'s discount code is: {code}',
            settings.EMAIL_HOST_USER,
            ['yahyabinusman7@gmail.com'],
            fail_silently=False,
        )
    else:
        code = existing_code.code
    
    return code

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product
from .forms import ProductForm
from django.db.models import Sum

@staff_member_required
def manage_products(request):
    products = Product.objects.all()
    total_products = products.count()
    total_quantity = products.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    
    # Handle search query if present
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    return render(request, 'store/manage_products.html', {
        'products': products,
        'total_products': total_products,
        'total_quantity': total_quantity,
        'search_query': search_query,
    })

@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_products')
    else:
        form = ProductForm()
    return render(request, 'store/add_edit_product.html', {'form': form})

@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('manage_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/add_edit_product.html', {'form': form, 'product': product})
