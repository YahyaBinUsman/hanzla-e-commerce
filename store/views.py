from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.core.mail import send_mail
from datetime import date, timedelta, datetime
from decimal import Decimal
from .models import Product, CartItem, Order, Review
from .forms import CheckoutForm, ReviewForm

# Home page view
def home(request):
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

# Add item to cart
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if product.quantity < quantity:
        # Handle case where requested quantity exceeds available quantity
        return redirect('product_list', category=product.category)

    cart_item, created = CartItem.objects.get_or_create(product=product)
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()

    product.update_quantity(-quantity)  # Deduct product quantity in inventory

    return redirect('view_cart')

# Checkout view
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

            # Set the delivery date to one day before the current date
            order.delivery_date = datetime.now().date() - timedelta(days=1)
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
            send_mail(
                admin_email_subject,
                email_body,
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
        # Retrieve the review token directly from the order
        review_token = order.review_token
        review_url = request.build_absolute_uri(f'/review/?token={review_token}')
        home_url = request.build_absolute_uri('/')
        
        email_subject = 'Delivery Confirmation'
        email_body = (
            f'Hello {order.first_name},\n\n'
            f'Your review token:\n'
            f'We hope you have received your order #{order.id}.\n'
            f'If yes, please leave a review here: {review_url}\n'
            f'If no, please contact us: {home_url}\n\n'
            f'Your review token: {review_token}\n'
            f'Your review token:\n'
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
        email_sent = True

    return JsonResponse({'email_sent': email_sent})

def order_confirmation(request):
    return render(request, 'store/order_confirmation.html')

# Order details page for admin
def order_details(request):
    orders = Order.objects.all()
    return render(request, 'store/order_details.html', {'orders': orders})

def review_page(request):
    token = request.GET.get('token')
    print(f"Token received: {token}")
    
    if not token:
        return HttpResponseBadRequest("Token is missing")

    try:
        order = Order.objects.get(review_token=token)
        print(f"Order found: {order}")
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Invalid token")

    product_names = [item.split(' (')[0] for item in order.products.split(', ')]
    print(f"Product names extracted: {product_names}")

    products = Product.objects.filter(name__in=product_names)
    print(f"Products retrieved: {products}")

    if request.method == 'POST':
        # Process individual product ratings
        ratings = {product_id: request.POST.get(f'rating_{product_id}') for product_id in products.values_list('id', flat=True)}
        print(f"Ratings received: {ratings}")

        for product_id, rating in ratings.items():
            if rating:
                product = get_object_or_404(Product, id=product_id)
                review = Review(product=product, name=request.POST.get(f'name_{product_id}'), description=request.POST.get(f'description_{product_id}'), rating=rating)
                review.save()
                product.update_average_rating()

        # Update testimonials page or perform other actions
        return redirect('review_page')  # Redirect to the same page after saving the review
    else:
        form = ReviewForm()
        print(f"Review form initialized: {form}")

    return render(request, 'store/review_page.html', {'products': products})


# Product list page
def product_list(request, category):
    products = Product.objects.filter(category=category)
    return render(request, 'store/product_list.html', {'products': products, 'category': category})

# Testimonials page
def testimonials(request):
    reviews = Review.objects.all()
    return render(request, 'store/testimonials.html', {'reviews': reviews})
