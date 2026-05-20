import streamlit as st
import stripe
from db import supabase

stripe.api_key = st.secrets.get("stripe", {}).get("secret_key", "")

def get_user_tier(user_id):
    try:
        res = supabase.table('profiles').select('subscription_tier').eq('id', user_id).maybe_single().execute()
        if res and res.data:
            return res.data.get('subscription_tier', 'free').lower()
        return 'free'
    except:
        return 'free'

def create_stripe_portal_session(user_email):
    if not stripe.api_key: return None
    try:
        customers = stripe.Customer.list(email=user_email, limit=1)
        if not customers.data: return None
        return stripe.billing_portal.Session.create(
            customer=customers.data[0].id,
            return_url="https://nync.app/?nav=Settings"
        ).url
    except: return None

def verify_stripe_payment(session_id):
    if not stripe.api_key: return None
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            line_item = stripe.checkout.Session.list_line_items(session_id, limit=1)
            return line_item.data[0].price.id
    except: return None

def create_stripe_checkout(user_email, price_id, success_url=None, cancel_url=None):
    if not stripe.api_key: return None
    if not success_url: success_url = "https://nync.app/?session_id={CHECKOUT_SESSION_ID}"
    if not cancel_url: cancel_url = "https://nync.app/"
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