from django.contrib import admin
from .models import Profile, Order, Trade, Wallet


class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', '_id', 'last_login', 'ip_address_list')


class OrderAdmin(admin.ModelAdmin):
	list_display = ('_id', 'user', 'order_status', 'type', 'created', 'modified')


class TradeAdmin(admin.ModelAdmin):
	list_display = ('_id', 'quantity', 'price', 'datetime')


class WalletAdmin(admin.ModelAdmin):
	list_display = ('user', '_id', 'btc_balance', 'usd_balance', 'btc_available', 'usd_available')

# Register your models here.
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Trade, TradeAdmin)