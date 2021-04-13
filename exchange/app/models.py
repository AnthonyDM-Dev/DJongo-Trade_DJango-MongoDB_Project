from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# From DJongo
from djongo.models.fields import ObjectIdField
from djongo import models

# Create your models here.
class Profile(models.Model):
	_id = ObjectIdField()
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	last_login = models.DateTimeField(default=timezone.now)
	ip_address_list = models.JSONField()


class Wallet(models.Model):
	_id = ObjectIdField()
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	btc_balance = models.FloatField()
	usd_balance = models.FloatField()
	btc_available = models.FloatField()
	usd_available = models.FloatField()

	def __str__(self):
		text = f'Wallet n. {self._id}. User owner: {self.user}'
		return text


class Order(models.Model):
	_id = ObjectIdField()
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	type = models.CharField(max_length=4)
	order_status = models.CharField(max_length=5)
	price_limit = models.FloatField()
	quantity = models.FloatField()
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)


class Trade(models.Model):
	_id = ObjectIdField()
	buyer_user = models.ForeignKey(User, related_name='buyer',on_delete=models.CASCADE)
	seller_user = models.ForeignKey(User, related_name='seller',on_delete=models.CASCADE)
	quantity = models.FloatField()
	price = models.FloatField()
	datetime = models.DateTimeField(auto_now_add=True)