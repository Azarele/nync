import streamlit as st
import requests
import datetime as dt
from db import supabase

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