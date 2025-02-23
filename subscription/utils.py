import random

import requests
from django.conf import settings

from subscription.models import Payment


def generate_invoice_id():
    invoice_id = str(random.randint(100000, 999999999999999))
    if Payment.objects.filter(invoice_id=invoice_id).exists():
        return generate_invoice_id()
    return invoice_id


def get_payment_token():
    url = "https://testoauth.homebank.kz/epay2/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "scope": "webapi usermanagement email_send verification statement statistics payment",
        "client_id": settings.CLIENT_ID,
        "client_secret": settings.CLIENT_SECRET,
    }
    response = requests.post(url, data=payload)
    response_data = response.json()
    return response_data.get("access_token")
