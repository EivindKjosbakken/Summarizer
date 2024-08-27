import streamlit as st
import stripe
import logging
import os
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# This is your test secret API key.
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
APP_URL = os.getenv("APP_URL")


def check_payment_status(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            return True
        else:
            return False
    except Exception as e:
        return False
    
def get_payment_amount(session_id):
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Retrieve the payment intent associated with the session
        payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
        
        # Get the amount paid (in the smallest currency unit, e.g., cents)
        amount_paid = payment_intent.amount_received
        currency = payment_intent.currency

        # Convert amount to a more human-readable format (e.g., dollars if in USD)
        amount_paid_in_dollars = amount_paid / 100 if currency == "usd" else amount_paid

        return amount_paid_in_dollars, currency

    except stripe.error.StripeError as e:
        # Handle error
        print(f"Error retrieving payment details: {e}")
        return None, None
   
def create_checkout_session():
    try:
        email = st.session_state.user_info["email"]
        session = stripe.checkout.Session.create(
            # ui_mode = 'embedded',
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': 'price_1PsSsWAIc3bSJAkEZJxviyud',
                    'quantity': 1,
                },
            ],
            mode='payment',
            # return_url="https://summarymate.streamlit.app/" + '/return.html?session_id={CHECKOUT_SESSION_ID}',
            # return_url="http://localhost:8504/" + '/return.html?session_id={CHECKOUT_SESSION_ID}',
            success_url = f"{APP_URL}?session_id={{CHECKOUT_SESSION_ID}}&email={email}",
            cancel_url=APP_URL

        )
        return session.url
    except Exception as e:
        return str(e)



