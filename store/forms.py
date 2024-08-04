from django import forms
from .models import CityDeliveryInfo, Order

from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    discount_code = forms.CharField(max_length=8, required=False, label='Discount Code')
    city = forms.ModelChoiceField(queryset=CityDeliveryInfo.objects.all(), required=True, label="City")


    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'postal_code', 'discount_code']

        widgets = {
            'payment_method': forms.HiddenInput(),
            'country': forms.HiddenInput(),
        }

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'description', 'rating']
