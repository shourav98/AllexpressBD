from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    pathao_city_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    pathao_zone_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    pathao_area_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'address_line_2','order_note', 'pathao_city_id', 'pathao_zone_id', 'pathao_area_id']

        # fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'address_line_2', 'country', 'state', 'city', 'order_note', 'pathao_city_id', 'pathao_zone_id', 'pathao_area_id']

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_method']


# from django import forms

# class OrderForm(forms.Form):
#     first_name = forms.CharField(max_length=50)
#     last_name = forms.CharField(max_length=50)
#     phone = forms.CharField(max_length=15)
#     email = forms.EmailField(max_length=50)
#     address_line_1 = forms.CharField(max_length=50)
#     address_line_2 = forms.CharField(max_length=50, required=False)
#     country = forms.CharField(max_length=50)
#     state = forms.CharField(max_length=50)
#     city = forms.CharField(max_length=50)
#     order_note = forms.CharField(max_length=100, required=False, widget=forms.Textarea)

# class PaymentMethodForm(forms.Form):
#     payment_method = forms.ChoiceField(choices=[('Cash on Delivery', 'Cash on Delivery'), ('SSLcommerz', 'SSLcommerz')])