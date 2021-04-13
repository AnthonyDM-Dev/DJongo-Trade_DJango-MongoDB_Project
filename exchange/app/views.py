from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
# From this app
from .market import Bot_CMC
from .models import Order, Wallet, Trade
from .forms import Order_Form
# Other imports
from bson import ObjectId


# Create your views here.
@login_required()
def order_view(request):
	# Orders lists
	buy_open_orders_list = Order.objects.filter(type='buy', order_status='open').order_by('-price_limit')
	sell_open_orders_list = Order.objects.filter(type='sell', order_status='open').order_by('price_limit')
	# Other data
	market_price = Bot_CMC().get_data()

	if request.method == 'POST':
		print(f'request.POST results:\n{ request.POST }')

		# Buy Order
		if request.POST.get('buy'):
			form = Order_Form(request.POST or None)
			if form.is_valid():
				type = 'buy'
				order_status = 'open'
				price_limit = form.cleaned_data.get('price_limit')
				quantity = form.cleaned_data.get('quantity')
				# Checking wallet availability.
				wallet_buyer = Wallet.objects.get(user=request.user)
				if wallet_buyer.usd_available >= (price_limit * quantity):
					wallet_buyer.usd_available -= (price_limit * quantity)
					wallet_buyer.save()
					# Order creation
					new_buy_order = Order.objects.create(user=request.user,
														 type=type,
														 order_status=order_status,
														 price_limit=price_limit,
														 quantity=quantity,
														 modified=timezone.now())
					# Order matching
					if sell_open_orders_list.exists():
						for num, sell_open_order in enumerate(sell_open_orders_list):
							if sell_open_order.price_limit <= new_buy_order.price_limit:
								print(f'Match found! Buy order id: {new_buy_order._id}.\n'
									  f'Sell order id: {sell_open_order._id}.\n'
									  f'Trade n: {num + 1}')

								# Trade conditions.
								if sell_open_order.quantity < new_buy_order.quantity:
									# Buy order partially filled. Sell order fully filled.
									btc_exchanged = sell_open_order.quantity
								elif sell_open_order.quantity >= new_buy_order.quantity:
									# Buy order fully filled. Sell order partially or fully filled.
									btc_exchanged = new_buy_order.quantity
								usd_exchanged = sell_open_order.price_limit
								real_depth = usd_exchanged * btc_exchanged

								# Buyer wallet.
								wallet_buyer = Wallet.objects.get(user=request.user)
								actual_buyer_btc = wallet_buyer.btc_balance
								actual_buyer_usd = wallet_buyer.usd_balance
								# Modifying wallet.
								wallet_buyer.usd_balance -= real_depth
								wallet_buyer.btc_balance += btc_exchanged
								wallet_buyer.usd_available += (new_buy_order.price_limit * btc_exchanged) - real_depth
								wallet_buyer.btc_available += btc_exchanged
								wallet_buyer.save()
								print(f'Wallet Buyer: {wallet_buyer.user}.\n'
									  f'BTC increased from {actual_buyer_btc} to {wallet_buyer.btc_balance};\n'
									  f'USD decreased from {actual_buyer_usd} to {wallet_buyer.usd_balance};')

								# Seller wallet.
								wallet_seller = Wallet.objects.get(user=sell_open_order.user)
								actual_seller_btc = wallet_seller.btc_balance
								actual_seller_usd = wallet_seller.usd_balance
								# Modifying wallet.
								wallet_seller.btc_balance -= btc_exchanged
								wallet_seller.usd_balance += real_depth
								wallet_seller.btc_available -= 0
								wallet_seller.usd_available += real_depth
								wallet_seller.save()
								print(f'Wallet Seller: {wallet_seller.user}.\n'
									  f'BTC decreased from {actual_seller_btc} to {wallet_seller.btc_balance};\n'
									  f'USD increased from {actual_seller_usd} to {wallet_seller.usd_balance};')

								# Trade creation.
								trade = Trade.objects.create(buyer_user=wallet_buyer.user,
															 seller_user=wallet_seller.user,
															 quantity=btc_exchanged,
															 price=usd_exchanged)

								# Modifying orders.
								if sell_open_order.quantity < new_buy_order.quantity:
									# Buy order still open. Updating bitcoins yet to be bought.
									actual_btc = new_buy_order.quantity
									new_buy_order.quantity -= btc_exchanged
									new_buy_order.save()
									print(f'Buy order id: {new_buy_order._id}. Status: {new_buy_order.order_status}.\n'
										  f'BTC before trade: {actual_btc}; BTC after trade: {new_buy_order.quantity};')
									# Sell order can close.
									sell_order = Order.objects.get(_id=sell_open_order._id)
									sell_order.order_status = 'close'
									sell_order.save()
									print(f'Sell order id: {sell_order._id}. Status: {sell_order.order_status}.')
								elif sell_open_order.quantity >= new_buy_order.quantity:
									# Buy order can close.
									new_buy_order.order_status = 'close'
									new_buy_order.save()
									print(f'Buy order id: {new_buy_order._id}. Status: {new_buy_order.order_status}.')
									if sell_open_order.quantity > new_buy_order.quantity:
										#Sell order still open. Updating bitcoins remaining to be sold.
										sell_order = Order.objects.get(_id=sell_open_order._id)
										actual_btc = sell_order.quantity
										sell_order.quantity -= btc_exchanged
										sell_order.save()
										print(f'Sell order id: {sell_order._id}. Status: {sell_order.order_status}.\n'
											  f'BTC before trade: {actual_btc}; BTC after trade: {sell_order.quantity};')
										messages.success(request, 'Your order has been totally executed! Congratulations!')
										return redirect('/exchange')
									elif sell_open_order.quantity == new_buy_order.quantity:
										#Sell order can close.
										sell_order = Order.objects.get(_id=sell_open_order._id)
										sell_order.order_status = 'close'
										sell_order.save()
										print(f'Sell order id: {sell_order._id}. Status: {sell_order.order_status}.')
										messages.success(request, 'Your order has been totally executed! Congratulations!')
										return redirect('/exchange')
							else:
								if num == 0:
									messages.success(request, 'Your order is successfully added to the Order Book!')
								elif num > 0:
									messages.success(request, (f'Your order is successfully added and already done {num} trades.'))
								return redirect('/exchange')
					else:
						messages.success(request, 'Your order is successfully added to the Order Book!')
						return redirect('/exchange')
				else:
					messages.error(request, 'Your balance is not enough.')
			else:
				messages.error(request, 'Order can not have negative values!')

		#Sell Order
		elif request.POST.get('sell'):
			form = Order_Form(request.POST or None)
			if form.is_valid():
				type = 'sell'
				order_status = 'open'
				price_limit = form.cleaned_data.get('price_limit')
				quantity = form.cleaned_data.get('quantity')
				# Checking wallet availability.
				wallet_seller = Wallet.objects.get(user=request.user)
				if wallet_seller.btc_available >= quantity:
					wallet_seller.btc_available -= quantity
					wallet_seller.save()
					# Order creation
					new_sell_order = Order.objects.create(user=request.user,
														  type=type,
														  order_status=order_status,
														  price_limit=price_limit,
														  quantity=quantity,
														  modified=timezone.now())
					# Order matching
					if buy_open_orders_list.exists():
						for num, buy_open_order in enumerate(buy_open_orders_list):
							if buy_open_order.price_limit >= new_sell_order.price_limit:
								print(f'Match found! Sell order id: {new_sell_order._id}.\n'
									  f'Buy order id: {buy_open_order._id}.\n'
									  f'Trade n: {num + 1}')
								# Trade conditions.
								if buy_open_order.quantity < new_sell_order.quantity:
									# Sell order partially filled. Buy order fully filled.
									btc_exchanged = buy_open_order.quantity
								elif buy_open_order.quantity >= new_sell_order.quantity:
									# Sell order fully filled. Buy order partially or fully filled.
									btc_exchanged = new_sell_order.quantity
								usd_exchanged = buy_open_order.price_limit
								real_depth = usd_exchanged * btc_exchanged

								# Seller wallet.
								wallet_seller = Wallet.objects.get(user=request.user)
								actual_seller_btc = wallet_seller.btc_balance
								actual_seller_usd = wallet_seller.usd_balance
								# Modifying wallet.
								wallet_seller.usd_balance += real_depth
								wallet_seller.btc_balance -= btc_exchanged
								wallet_seller.usd_available += real_depth
								wallet_seller.btc_available += 0
								wallet_seller.save()
								print(f'Wallet Seller: {wallet_seller.user}.\n'
									  f'BTC decreased from {actual_seller_btc} to {wallet_seller.btc_balance};\n'
									  f'USD increased from {actual_seller_usd} to {wallet_seller.usd_balance};')

								# Buyer wallet.
								wallet_buyer = Wallet.objects.get(user=buy_open_order.user)
								actual_buyer_btc = wallet_buyer.btc_balance
								actual_buyer_usd = wallet_buyer.usd_balance
								# Modifying wallet.
								wallet_buyer.btc_balance += btc_exchanged
								wallet_buyer.usd_balance -= real_depth
								wallet_buyer.btc_available += btc_exchanged
								wallet_buyer.usd_available += (buy_open_order.price_limit * btc_exchanged) - real_depth
								wallet_buyer.save()
								print(f'Wallet Buyer: {wallet_buyer.user}.\n'
									  f'BTC increased from {actual_buyer_btc} to {wallet_buyer.btc_balance};\n'
									  f'USD decreased from {actual_buyer_usd} to {wallet_buyer.usd_balance};')

								# Trade creation.
								trade = Trade.objects.create(buyer_user=wallet_buyer.user,
															 seller_user=wallet_seller.user,
															 quantity=btc_exchanged,
															 price=usd_exchanged)

								# Modifying orders.
								if buy_open_order.quantity < new_sell_order.quantity:
									# Sell order still open. Updating bitcoins yet to be sold.
									actual_btc = new_sell_order.quantity
									new_sell_order.quantity -= btc_exchanged
									new_sell_order.save()
									print(f'Sell order id: {new_sell_order._id}. Status: {new_sell_order.order_status}.\n'
										  f'BTC before trade: {actual_btc}; BTC after trade: {new_sell_order.quantity};')
									# Buy order can close.
									buy_order = Order.objects.get(_id=buy_open_order._id)
									buy_order.order_status = 'close'
									buy_order.save()
									print(f'Buy order id: {buy_order._id}. Status: {buy_order.order_status}.')
								elif buy_open_order.quantity >= new_sell_order.quantity:
									# Sell order can close.
									new_sell_order.order_status = 'close'
									new_sell_order.save()
									print(f'Sell order id: {new_sell_order._id}. Status: {new_sell_order.order_status}.')
									if buy_open_order.quantity > new_sell_order.quantity:
										# Buy order still open. Updating bitcoins remaining to buy.
										buy_order = Order.objects.get(_id=buy_open_order._id)
										actual_btc = buy_order.quantity
										buy_order.quantity -= btc_exchanged
										buy_order.save()
										print(f'Buy order id: {buy_order._id}. Status: {buy_order.order_status}.\n'
											  f'BTC before trade: {actual_btc}; BTC after trade: {buy_order.quantity};')
										messages.success(request, 'Your order has been totally executed! Congratulations!')
										return redirect('/exchange')
									elif buy_open_order.quantity == new_sell_order.quantity:
										# Buy order can close.
										buy_order = Order.objects.get(_id=buy_open_order._id)
										buy_order.order_status = 'close'
										buy_order.save()
										print(f'Buy order id: {buy_order._id}. Status: {buy_order.order_status}.')
										messages.success(request, 'Your order has been totally executed! Congratulations!')
										return redirect('/exchange')
							else:
								if num == 0:
									messages.success(request, (f'Your order is successfully added to the Order Book.'))
								elif num > 0:
									messages.success(request, (f'Your order is successfully added and done {num} trades.'))
								return redirect('/exchange')
					else:
						messages.success(request, 'Your order is successfully added to the Order Book!')
						return redirect('/exchange')
				else:
					messages.error(request, 'Your balance is not enough.')
			else:
				messages.error(request, 'Order can not have negative values!')

		# Delete Order
		elif request.POST.get('delete'):
			_id = ObjectId(request.POST['delete'])
			order = Order.objects.get(_id=_id)
			wallet_to_restore = Wallet.objects.get(user=order.user)
			if order.type == 'buy':
				wallet_to_restore.usd_available += (order.price_limit * order.quantity)
				wallet_to_restore.save()
			elif order.type == 'sell':
				wallet_to_restore.btc_available += order.quantity
				wallet_to_restore.save()
			print(f'The order n.{order._id} is going to be deleted...\n...\n...')
			order.delete()
			print(f'Order deleted. Verify: {order}')
			messages.success(request, 'Your order has been deleted successfully!')
			return redirect('/exchange')

	# Orders lists refresh
	buy_open_orders_list = Order.objects.filter(type='buy', order_status='open').order_by('-price_limit')
	sell_open_orders_list = Order.objects.filter(type='sell', order_status='open').order_by('price_limit')
	form = Order_Form()
	user_wallet = Wallet.objects.get(user=request.user)
	# Getting latest trade price
	all_trades = Trade.objects.all().order_by('-datetime')
	if all_trades.exists():
		last_price = all_trades[0].price
	else:
		last_price = 'empty'


	return render(request, 'app/app_exchange_view.html', {'form': form,
														  'buy_open_orders_list': buy_open_orders_list,
														  'sell_open_orders_list': sell_open_orders_list,
														  'user_wallet': user_wallet,
														  'market_price': market_price,
														  'last_price': last_price,
														  'all_trades': all_trades,
														  })

def json_all_orders_view(request):
	if request.user.is_staff:
		open_orders = Order.objects.filter(order_status='open').order_by('-created')
		qs_buy = []
		qs_sell = []
		for order in open_orders:
			single_order = {'order_id': str(order._id),
							'user': str(order.user),
							'order_type': order.type,
							'price_limit': order.price_limit,
							'quantity': order.quantity,
							'creation_date': order.created}
			if order.type == 'buy':
				qs_buy.append(single_order)
			elif order.type == 'sell':
				qs_sell.append(single_order)
		json_report = {'order_book':
						   {'buy_orders': qs_buy,
							'sell_orders': qs_sell,}
					   }
	else:
		return redirect('/permission_denied')
	return JsonResponse(json_report, safe=False)