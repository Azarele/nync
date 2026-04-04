import streamlit as st
import stripe

def create_stripe_portal_session(user_email):
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    try:
        customers = stripe.Customer.list(email=user_email, limit=1)
        if not customers.data: return None
        return stripe.billing_portal.Session.create(
            customer=customers.data[0].id,
            return_url="https://nync.app/?nav=Settings"
        ).url
    except: return None

def verify_stripe_payment(session_id):
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            line_item = stripe.checkout.Session.list_line_items(session_id, limit=1)
            return line_item.data[0].price.id
    except: return None

def create_stripe_checkout(user_email, price_id, success_url=None, cancel_url=None):
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    base_url = "https://nync.app/"
    if not success_url: success_url = f"{base_url}/?stripe_session_id={{CHECKOUT_SESSION_ID}}"
    if not cancel_url: cancel_url = f"{base_url}/?nav=Pricing"
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            customer_email=user_email,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
    except: return None