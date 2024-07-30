from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, CartItem, CheckoutInfo
from django.db.models import F

def home(request):
    return render(request, 'store/home.html')

def product_list(request, category):
    products = Product.objects.filter(category=category)
    return render(request, 'store/product_list.html', {'products': products, 'category': category})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, CartItem
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, CartItem
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, CartItem
from decimal import Decimal

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

from django.shortcuts import render, redirect
from django.core.mail import send_mail
from .models import CartItem, Order
from .forms import CheckoutForm
from datetime import timedelta
from decimal import Decimal

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

            if cart_items.exists():
                max_delivery_time = max([item.product.delivery_time for item in cart_items])
                order.delivery_date = order.order_date + timedelta(days=max_delivery_time)
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
                f'Products:\n{order.products}'
            )
            send_mail(
                email_subject,
                email_body,
                'from@example.com',
                [order.email],
                fail_silently=False,
            )

            # Send email to admin
            admin_email_subject = 'New Order Confirmation'
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

def order_confirmation(request):
    return render(request, 'store/order_confirmation.html')

from django.shortcuts import render
from .models import Order

def order_details(request):
    orders = Order.objects.all()
    return render(request, 'store/order_details.html', {'orders': orders})


def review_page(request):
    return render(request, 'store/review_page.html')

from django.http import JsonResponse
from datetime import date
from .models import Order
from django.core.mail import send_mail

def check_delivery_dates(request):
    today = date.today()
    orders = Order.objects.filter(delivery_date__lt=today, review_email_sent=False)

    email_sent = False
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
        email_sent = True

    return JsonResponse({'email_sent': email_sent})
