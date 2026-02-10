import streamlit as st
import requests
import datetime as dt
import stripe
from supabase import create_client

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_supabase():
    try:
        if "supabase" not in st.secrets: return None
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except: return None

supabase = get_supabase()

# --- AUTH HELPER FUNCTIONS ---
def login_user(email, password):
    if not supabase: return False
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            st.session_state.session = res.session
            st.session_state.user = res.user
            return True # <--- RETURNS TRUE, DOES NOT RERUN
    except Exception as e: 
        st.warning(f"Login failed: {e}")
    return False

def signup_user(email, password):
    if not supabase: return False
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.session:
            st.session_state.session = res.session
            st.session_state.user = res.user
            return True # <--- RETURNS TRUE
        else: 
            st.info("Check email to confirm.")
    except Exception as e: 
        st.warning(f"Sign up failed: {e}")
    return False

@st.cache_data(ttl=300)
def get_user_profile(user_id):
    try: return supabase.table('profiles').select('*').eq('id', user_id).single().execute().data
    except: return None

def get_tier_level(tier_name):
    """Converts tier name to a number for comparison"""
    tiers = {'free': 0, 'squad': 1, 'guild': 2, 'empire': 3}
    return tiers.get(str(tier_name).lower(), 0)

# --- MICROSOFT AUTH ---
def get_microsoft_url(user_id):
    try:
        client_id = st.secrets["microsoft"]["client_id"]
        redirect_uri = st.secrets["microsoft"]["redirect_uri"]
        authority = st.secrets["microsoft"]["authority"]
        scope = "Calendars.ReadWrite offline_access User.Read"
        state = f"microsoft_connect:{user_id}"
        return (f"{authority}/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}&state={state}")
    except: return "#"

def handle_microsoft_callback(code, user_id):
    try:
        token_url = f"{st.secrets['microsoft']['authority']}/oauth2/v2.0/token"
        payload = {
            "client_id": st.secrets["microsoft"]["client_id"],
            "scope": "Calendars.ReadWrite offline_access User.Read",
            "code": code,
            "redirect_uri": st.secrets["microsoft"]["redirect_uri"],
            "grant_type": "authorization_code",
            "client_secret": st.secrets["microsoft"]["client_secret"],
        }
        r = requests.post(token_url, data=payload)
        tokens = r.json()
        
        if "access_token" not in tokens: return False
            
        data = {
            "user_id": user_id, "provider": "outlook",
            "access_token": tokens["access_token"], 
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in")
        }
        
        try:
            existing = supabase.table("calendar_connections").select("id").eq("user_id", user_id).eq("provider", "outlook").execute()
            if existing.data:
                supabase.table("calendar_connections").update(data).eq("user_id", user_id).eq("provider", "outlook").execute()
            else:
                supabase.table("calendar_connections").insert(data).execute()
            return True
        except: return False
    except: return False

def refresh_outlook_token(user_id):
    if not supabase: return None
    try:
        record = supabase.table("calendar_connections").select("*").eq("user_id", user_id).eq("provider", "outlook").single().execute()
        if not record.data: return None
        refresh_token = record.data.get("refresh_token")
        
        token_url = f"{st.secrets['microsoft']['authority']}/oauth2/v2.0/token"
        payload = {
            "client_id": st.secrets["microsoft"]["client_id"],
            "client_secret": st.secrets["microsoft"]["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "Calendars.ReadWrite offline_access User.Read"
        }
        r = requests.post(token_url, data=payload)
        new_tokens = r.json()
        if "access_token" not in new_tokens: return None
            
        supabase.table("calendar_connections").update({
            "access_token": new_tokens["access_token"],
            "refresh_token": new_tokens.get("refresh_token", refresh_token),
            "expires_in": new_tokens.get("expires_in")
        }).eq("user_id", user_id).execute()
        return new_tokens["access_token"]
    except: return None

def fetch_outlook_events(user_id, start_dt, end_dt):
    if not supabase or not user_id: return []
    try:
        response = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", "outlook").maybe_single().execute()
        if not response or not response.data: return []
        token = response.data.get('access_token')

        headers = {"Authorization": f"Bearer {token}", "Prefer": "outlook.timezone=\"UTC\""}
        start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        endpoint = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={start_str}&endDateTime={end_str}&$select=subject,start,end,showAs"
        
        r = requests.get(endpoint, headers=headers)
        if r.status_code == 401:
            new_token = refresh_outlook_token(user_id)
            if new_token:
                headers["Authorization"] = f"Bearer {new_token}"
                r = requests.get(endpoint, headers=headers)
            else: return [] 
        if r.status_code != 200: return []
        
        events = r.json().get('value', [])
        blocked_hours = []
        for e in events:
            start = dt.datetime.fromisoformat(e['start']['dateTime'].replace('Z', '+00:00'))
            end = dt.datetime.fromisoformat(e['end']['dateTime'].replace('Z', '+00:00'))
            curr = start
            while curr < end:
                blocked_hours.append(curr.replace(minute=0, second=0, microsecond=0))
                curr += dt.timedelta(hours=1)
        return blocked_hours
    except: return []

def book_outlook_meeting(user_id, subject, start_dt_utc, duration_minutes, attendees):
    if not supabase: return False
    try:
        token = refresh_outlook_token(user_id) 
        if not token: return False

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        end_dt_utc = start_dt_utc + dt.timedelta(minutes=duration_minutes)
        
        attendee_list = [{"emailAddress": {"address": email}, "type": "required"} for email in attendees]

        payload = {
            "subject": subject,
            "start": {"dateTime": start_dt_utc.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_dt_utc.isoformat(), "timeZone": "UTC"},
            "attendees": attendee_list,
            "isOnlineMeeting": True, 
            "onlineMeetingProvider": "teamsForBusiness" 
        }

        r = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=payload)
        return r.status_code in [201, 200]
    except: return False

# --- GOOGLE AUTH ---
def get_google_url():
    try:
        base_url = "https://nyncapp.streamlit.app/"
        params = []
        if "invite" in st.query_params: params.append(f"invite={st.query_params['invite']}")
        
        redirect_url = f"{base_url}/?{'&'.join(params)}" if params else base_url
        
        data = supabase.auth.sign_in_with_oauth({
            "provider": "google", 
            "options": {
                "redirect_to": redirect_url,
                "queryParams": {
                    "access_type": "offline", 
                    "prompt": "consent",
                    "scope": "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/userinfo.email"
                }
            }
        })
        return data.url
    except: return None

def save_google_token(user_id, session):
    try:
        if not session.provider_token: return False
        
        data = {
            "user_id": user_id, 
            "provider": "google",
            "access_token": session.provider_token,
            "refresh_token": session.provider_refresh_token, 
            "expires_in": 3599 
        }

        existing = supabase.table("calendar_connections").select("id").eq("user_id", user_id).eq("provider", "google").execute()
        if existing.data:
            supabase.table("calendar_connections").update(data).eq("user_id", user_id).eq("provider", "google").execute()
        else:
            supabase.table("calendar_connections").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error saving Google Token: {e}")
        return False

def refresh_google_token(user_id):
    if not supabase: return None
    try:
        record = supabase.table("calendar_connections").select("*").eq("user_id", user_id).eq("provider", "google").single().execute()
        if not record.data or not record.data.get("refresh_token"): return None
        
        if "google" not in st.secrets: return None
        
        refresh_token = record.data.get("refresh_token")
        token_url = "https://oauth2.googleapis.com/token"
        
        payload = {
            "client_id": st.secrets["google"]["client_id"],
            "client_secret": st.secrets["google"]["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        r = requests.post(token_url, data=payload)
        new_tokens = r.json()
        
        if "access_token" not in new_tokens: return None
        
        supabase.table("calendar_connections").update({
            "access_token": new_tokens["access_token"],
            "expires_in": new_tokens.get("expires_in", 3599)
        }).eq("user_id", user_id).eq("provider", "google").execute()
        
        return new_tokens["access_token"]
    except: return None

def fetch_google_events(user_id, start_dt, end_dt):
    if not supabase or not user_id: return []
    try:
        response = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", "google").maybe_single().execute()
        if not response or not response.data: return []
        token = response.data.get('access_token')

        start_str = start_dt.isoformat() + "Z"
        end_str = end_dt.isoformat() + "Z"
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={start_str}&timeMax={end_str}&singleEvents=true"
        headers = {"Authorization": f"Bearer {token}"}
        
        r = requests.get(url, headers=headers)
        
        if r.status_code == 401:
            new_token = refresh_google_token(user_id)
            if new_token:
                headers = {"Authorization": f"Bearer {new_token}"}
                r = requests.get(url, headers=headers)
            else: return []

        if r.status_code != 200: return []
        
        items = r.json().get('items', [])
        blocked_hours = []
        for i in items:
            if 'dateTime' not in i.get('start', {}): continue
            
            start = dt.datetime.fromisoformat(i['start']['dateTime'])
            end = dt.datetime.fromisoformat(i['end']['dateTime'])
            
            if start.tzinfo: start = start.astimezone(dt.timezone.utc).replace(tzinfo=None)
            if end.tzinfo: end = end.astimezone(dt.timezone.utc).replace(tzinfo=None)
            
            curr = start
            while curr < end:
                blocked_hours.append(curr.replace(minute=0, second=0, microsecond=0))
                curr += dt.timedelta(hours=1)
                
        return blocked_hours
    except: return []

def restore_session(access_token, refresh_token):
    if not supabase: return None
    try:
        res = supabase.auth.set_session(access_token, refresh_token)
        if res.user:
            return res.session
    except:
        return None
    return None

# --- TEAM & UTILS ---
@st.cache_data(ttl=60)
def get_martyr_stats(team_id):
    if not supabase: return []
    try:
        resp = supabase.table("pain_ledger").select("user_email, pain_score").eq("team_id", team_id).execute()
        totals = {}
        for row in resp.data:
            e = row['user_email']
            p = row['pain_score']
            totals[e] = totals.get(e, 0) + p
        leaderboard = [{"email": k, "total_pain": v} for k, v in totals.items()]
        leaderboard.sort(key=lambda x: x['total_pain'], reverse=True)
        return leaderboard
    except: return []

@st.cache_data(ttl=60)
def get_user_teams(user_id):
    try:
        resp = supabase.table('team_members').select('team_id, teams(name, invite_code)').eq('user_id', user_id).execute()
        return {item['teams']['name']: item['team_id'] for item in resp.data if item['teams']}
    except: return {}

@st.cache_data(ttl=60)
def get_team_roster(team_id):
    roster = []
    try:
        real = supabase.table('team_members').select('user_id, profiles(email, default_timezone)').eq('team_id', team_id).not_.is_('user_id', 'null').execute()
        for r in real.data:
            if r['profiles']:
                roster.append({'email': r['profiles']['email'], 'tz': r['profiles']['default_timezone'] or 'UTC', 'type': 'user', 'name': r['profiles']['email'].split('@')[0]})
        ghost = supabase.table('team_members').select('ghost_name, ghost_email, ghost_timezone').eq('team_id', team_id).is_('user_id', 'null').execute()
        for g in ghost.data:
            roster.append({'email': g.get('ghost_email') or g.get('ghost_name'), 'tz': g['ghost_timezone'], 'type': 'ghost', 'name': g.get('ghost_name', 'Ghost')})
        return roster
    except: return []

def check_team_status(team_id):
    try:
        team = supabase.table('teams').select('trial_ends_at').eq('id', team_id).single().execute()
        if not team.data: return 'active'
        trial_end_str = team.data.get('trial_ends_at')
        if not trial_end_str: return 'active'
        trial_end = dt.datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
        is_expired = dt.datetime.now(trial_end.tzinfo) > trial_end
        count = supabase.table('team_members').select('*', count='exact').eq('team_id', team_id).execute().count
        if is_expired and count > 3: return 'locked'
        return 'active'
    except: return 'active'

def join_team_by_code(user_id, code):
    try:
        t = supabase.table('teams').select('id, name').eq('invite_code', code).execute()
        if not t.data: return False
        tid, name = t.data[0]['id'], t.data[0]['name']
        if supabase.table('team_members').select('*').eq('team_id', tid).eq('user_id', user_id).execute().data: return True
        supabase.table('team_members').insert({'team_id': tid, 'user_id': user_id}).execute()
        st.session_state.active_team = name
        get_user_teams.clear() 
        return True
    except: return False

def create_team(user_id, name):
    import secrets, string
    code = "NYNC-" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    try:
        t = supabase.table('teams').insert({'name': name, 'invite_code': code, 'created_by': user_id}).execute()
        if not t.data: return False
        tid = t.data[0]['id']
        supabase.table('team_members').insert({'team_id': tid, 'user_id': user_id, 'role': 'admin'}).execute()
        st.session_state.active_team = name
        get_user_teams.clear()
        return True
    except: return False

def create_stripe_portal_session(user_email):
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    try:
        customers = stripe.Customer.list(email=user_email, limit=1)
        if not customers.data: return None
        return stripe.billing_portal.Session.create(
            customer=customers.data[0].id,
            return_url="https://nyncapp.streamlit.app/?nav=Settings"
        ).url
    except: return None

def delete_user_data(user_id):
    try:
        supabase.table('calendar_connections').delete().eq('user_id', user_id).execute()
        supabase.table('team_members').delete().eq('user_id', user_id).execute()
        supabase.table('profiles').delete().eq('id', user_id).execute()
        return True
    except: return False

def verify_stripe_payment(session_id):
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            line_item = stripe.checkout.Session.list_line_items(session_id, limit=1)
            return line_item.data[0].price.id
    except: return None

def upgrade_user_tier(user_id, tier_name):
    try:
        supabase.table('profiles').update({'subscription_tier': tier_name}).eq('id', user_id).execute()
        get_user_profile.clear()
        return True
    except: return False

def create_stripe_checkout(user_email, price_id, success_url=None, cancel_url=None):
    if "stripe" not in st.secrets: return None
    stripe.api_key = st.secrets["stripe"]["secret_key"]
    base_url = "https://nyncapp.streamlit.app"
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