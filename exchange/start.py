#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exchange.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(['start.py', 'migrate'])

    from django.contrib.auth.models import User
    from app.models import Wallet, Profile
    from app.utils import btc_assignment, usd_assignment
    from django.utils import timezone

    btc = btc_assignment()
    usd = usd_assignment()

    # SuperUser creation:
    admin = User.objects.create_superuser('admin', 'admin@admin.it', 'admin')
    profile = Profile.objects.create(user=admin,
                                     last_login=timezone.now(),
                                     ip_address_list=['127.0.0.1'])
    wallet = Wallet.objects.create(user=admin,
                                   btc_balance=btc,
                                   usd_balance=usd,
                                   btc_available=btc,
                                   usd_available=usd)
    print('MIGRATION AND SUPERUSER CREATION DONE!\nSUPERUSER CREDENTIALS:\nUsername: admin\nPassword: admin')

if __name__ == '__main__':
    main()
