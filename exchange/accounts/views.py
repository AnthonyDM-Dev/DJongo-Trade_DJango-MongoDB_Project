from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
# From this app
from .forms import Login_Form, Register_Form, Password_Form
from .utils import get_ip_address
# Other apps import
from app.models import Profile, Wallet, Order, Trade
from app.utils import btc_assignment, usd_assignment
# Other imports
from bson import ObjectId


User = get_user_model()
# Create your views here.
def homepage_view(request):
	return render(request, 'accounts/accounts_homepage_view.html', {})

def login_view(request):
	if request.method == 'POST':
		if request.POST.get('next'):
			next = request.POST.get('next')
		else:
			next = ''
		form = Login_Form(request.POST or None)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			# Authentication
			user = authenticate(request, username=username, password=password)
			if user != None:
				login(request, user)
				profile = Profile.objects.get(user=user)
				profile.last_login = timezone.now()
				profile.save()
				# IP address check
				ip_address = get_ip_address(request)
				if profile.ip_address_list == []:
					profile.ip_address_list.append(ip_address)
					profile.save()
				else:
					pass
				if ip_address not in profile.ip_address_list:
					return redirect(f"/ip_check/?next={next}")
				elif next != '':
					return redirect(next)
				else:
					return redirect('/')
	else:
		form = Login_Form()
	return render(request, 'accounts/accounts_login_form.html', {'form': form,
																 })

def logout_view(request):
	logout(request)
	return redirect('/login')

def register_view(request):
	if request.method == 'POST':
		form = Register_Form(request.POST or None)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			first_name = form.cleaned_data.get('first_name')
			last_name = form.cleaned_data.get('last_name')
			email = form.cleaned_data.get('email')
			password = form.cleaned_data.get('password')
			try:
				user = User.objects.create_user(username, email, password, first_name=first_name, last_name=last_name)
			except:
				user = None
			if user != None:
				# Profile creation
				ip_address = get_ip_address(request)
				ip_list = []
				last_login = timezone.now()
				profile = Profile.objects.create(user=user,
												 last_login=last_login,
												 ip_address_list=ip_list)
				profile.ip_address_list.append(ip_address)
				profile.save()
				# Wallet creation
				btc_balance = btc_assignment()
				usd_balance = usd_assignment()
				wallet = Wallet.objects.create(user=user,
											   btc_balance=btc_balance,
											   usd_balance=usd_balance,
											   btc_available=btc_balance,
											   usd_available=usd_balance)
				wallet.save()
				login(request, user)
				return redirect('/')
	else:
		form = Register_Form()
	return render(request, 'accounts/accounts_register_form.html', {'form': form,
																	})

@login_required()
def user_profile_view(request, id):
	user_obj = get_object_or_404(User, id=id)
	if request.user.is_staff:
		profile_info = Profile.objects.get(user=user_obj)
		orders_info = Order.objects.filter(user=user_obj)
		wallet_info = Wallet.objects.get(user=user_obj)
	else:
		if request.user.id == user_obj.id:
			profile_info = Profile.objects.get(user=user_obj)
			orders_info = Order.objects.filter(user=user_obj)
			wallet_info = Wallet.objects.get(user=user_obj)
		else:
			return redirect('/permission_denied')
	# Profit calculation. Sell trades - Buy trades.
	all_sell_trades = Trade.objects.filter(seller_user=user_obj)
	all_buy_trades = Trade.objects.filter(buyer_user=user_obj)
	sell_depth_list = []
	buy_depth_list = []
	for sell_trade in all_sell_trades:
		depth = sell_trade.quantity * sell_trade.price
		sell_depth_list.append(depth)
	for buy_trade in all_buy_trades:
		depth = buy_trade.quantity * buy_trade.price
		buy_depth_list.append(depth)
	profit_usd = sum(sell_depth_list) - sum(buy_depth_list)
	# Tables
	open_orders = Order.objects.filter(user=user_obj, order_status='open').order_by('-created')
	user_trades = Trade.objects.filter(Q(buyer_user=user_obj)|
									   Q(seller_user=user_obj)
									   ).distinct().order_by('-datetime')
	# Delete Order
	if request.POST.get('delete'):
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
	return render(request, 'accounts/accounts_user_profile.html', {'user_obj': user_obj,
																   'profile_info': profile_info,
																   'orders_info': orders_info,
																   'wallet_info': wallet_info,
																   'open_orders': open_orders,
																   'user_trades': user_trades,
																   'profit_usd': profit_usd,
																   }
				  )

@login_required()
def json_profile_view(request, id):
	user_obj = get_object_or_404(User, id=id)
	if (request.user.id == user_obj.id) or (request.user.is_staff):
		# Orders report
		orders = Order.objects.filter(user_id=id).order_by('-created')
		qs_open = []
		for order in orders:
			if order.order_status == 'open':
				single_order = {'order_id': str(order._id),
								'order_type': order.type,
								'price_limit': order.price_limit,
								'quantity': order.quantity,
								'creation_date': order.created}
				qs_open.append(single_order)
		# Trades report
		trades = Trade.objects.filter(Q(buyer_user=user_obj)|
									  Q(seller_user=user_obj)
									  ).distinct().order_by('-datetime')
		qs_trades = []
		for trade in trades:
			if trade.buyer_user == trade.seller_user:
				type = 'buy & sell'
			elif trade.buyer_user == user_obj:
				type = 'buy'
			else:
				type = 'sell'
			single_trade = {'trade_id': str(trade._id),
							'type': type,
							'price': trade.price,
							'quantity': trade.quantity,
							'date': trade.datetime}
			qs_trades.append(single_trade)
		# Json report
		json_report = {'user': f'{user_obj.username}',
					   'open_orders': qs_open,
					   'trades': qs_trades
					   }
	else:
		return redirect('/permission_denied')
	return JsonResponse(json_report, safe=False)

def permission_denied_view(request):
	return render(request, 'accounts/accounts_permission_denied.html', {})

@login_required()
def change_password_view(request):
	initial_data = {
		'username': request.user
	}
	if request.method == 'POST':
		form = Password_Form(request.POST or None, initial=initial_data)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			new_password = form.cleaned_data.get('new_password')
			user = authenticate(request, username=username, password=password)
			if user != None:
				user_update = User.objects.get(username=username)
				user_update.set_password(new_password)
				user_update.save()
				return redirect('/password_changed')
	else:
		form = Password_Form(initial=initial_data)
	return render(request, 'accounts/accounts_password_form.html', {'form': form})

def password_changed_view(request):
	context = {}
	return render(request, 'accounts/accounts_password_changed.html', context)

@login_required()
def ip_check_view(request):
	ip_address = get_ip_address(request)
	if request.method == 'POST':
		if request.POST.get('yes'):
			profile = Profile.objects.get(user=request.user)
			profile.ip_address_list.append(ip_address)
			profile.save()
			messages.success(request, 'IP address added to your safe device list!')
		elif request.POST.get('no'):
			return redirect('/')
	return render(request, 'accounts/accounts_ipcheck_view.html', {})