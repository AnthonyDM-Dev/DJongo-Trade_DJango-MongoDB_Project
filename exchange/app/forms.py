from django import forms


class Order_Form(forms.Form):
	price_limit = forms.FloatField(widget=forms.TextInput(attrs={'class': 'white-text'}))
	quantity = forms.FloatField(widget=forms.TextInput(attrs={'class': 'white-text'}))

	def clean(self):
			cleaned_data = super().clean()
			price_limit = self.cleaned_data.get('price_limit')
			quantity = self.cleaned_data.get('quantity')
			order_type = self.cleaned_data.get('order_type')
			if price_limit < 0:
				raise forms.ValidationError('') #display messages.error instead
			if quantity < 0:
				raise forms.ValidationError('') #display messages.error instead
			return cleaned_data