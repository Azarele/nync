import streamlit as st
import requests
import datetime as dt
import re
from db import supabase

# --- SAFE EMAIL VALIDATOR ---
def is_valid_email(email):
    """Prevents garbage strings from crashing the Google/Microsoft APIs"""
    if not email: return False
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", str(email).strip()))

def get_provider_token(user_id, provider):
    """Safely retrieves the CURRENT access token without forcing a refresh"""
    if not supabase: return None
    try:
        res = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", provider).maybe_single().execute()
        if res and res.data: return res.data.get("access_token")
        return None
    except: return None

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
        r = requests.post(token_url, data=payload, timeout=10)
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
        r = requests.post(token_url, data=payload, timeout=10)
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
        
        try:
            r = requests.get(endpoint, headers=headers, timeout=5)
            if r.status_code == 401:
                new_token = refresh_outlook_token(user_id)
                if new_token:
                    headers["Authorization"] = f"Bearer {new_token}"
                    r = requests.get(endpoint, headers=headers, timeout=5)
                else: return [] 
            if r.status_code != 200:
                st.toast("⚠️ Could not sync live Outlook calendar, using cached availability.")
                return []
        except requests.exceptions.Timeout:
            st.toast("⏱️ Outlook API timed out, using cached availability.")
            return []
        except Exception:
            st.toast("⚠️ Could not sync live Outlook calendar, using cached availability.")
            return []
        
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
    if not supabase: return False, None
    try:
        token = get_provider_token(user_id, "outlook") 
        if not token: return False, None

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        end_dt_utc = start_dt_utc + dt.timedelta(minutes=duration_minutes)
        
        attendee_list = [{"emailAddress": {"address": email.strip()}, "type": "required"} for email in attendees if is_valid_email(email)]

        start_str = start_dt_utc.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_dt_utc.strftime("%Y-%m-%dT%H:%M:%S")

        payload = {
            "subject": subject,
            "start": {"dateTime": start_str, "timeZone": "UTC"},
            "end": {"dateTime": end_str, "timeZone": "UTC"},
            "attendees": attendee_list,
            "isOnlineMeeting": True 
        }

        r = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=payload, timeout=10)
        
        if r.status_code == 401:
            token = refresh_outlook_token(user_id)
            if token:
                headers["Authorization"] = f"Bearer {token}"
                r = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=payload, timeout=10)

        if r.status_code in [201, 200]:
            return True, r.json().get("onlineMeeting", {}).get("joinUrl")
        else:
            st.toast(f"Outlook Error {r.status_code}: {r.json().get('error', {}).get('message', 'Unknown')}")
            return False, None
    except Exception as e: 
        print(f"Failed to book outlook meeting: {e}")
        return False, None


# --- GOOGLE AUTH ---
def get_google_url():
    try:
        base_url = "https://nyncapp.streamlit.app/"
        params = []
        if "invite" in st.query_params: params.append(f"invite={st.query_params['invite']}")
        
        redirect_url = f"{base_url}/?{'&'.join(params)}" if params else base_url
        
        # FIX: Reverted to the safer, limited scopes (Events read/write + Profile read-only)
        data = supabase.auth.sign_in_with_oauth({
            "provider": "google", 
            "options": {
                "redirect_to": redirect_url,
                "scopes": "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/userinfo.email",
                "queryParams": {
                    "access_type": "offline", 
                    "prompt": "consent"
                }
            }
        })
        return data.url
    except: return None

def save_google_token(user_id, session):
    try:
        if not getattr(session, 'provider_token', None): return False
        
        existing = supabase.table("calendar_connections").select("id, refresh_token").eq("user_id", user_id).eq("provider", "google").execute()
        
        ref_token = getattr(session, 'provider_refresh_token', None)
        if existing.data and not ref_token:
            ref_token = existing.data[0].get("refresh_token")

        data = {
            "user_id": user_id, 
            "provider": "google",
            "access_token": session.provider_token,
            "refresh_token": ref_token, 
            "expires_in": 3599 
        }

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
        if not record.data or not record.data.get("refresh_token"): 
            return None
        
        if "google" not in st.secrets: return None
        
        refresh_token = record.data.get("refresh_token")
        token_url = "https://oauth2.googleapis.com/token"
        
        payload = {
            "client_id": st.secrets["google"]["client_id"],
            "client_secret": st.secrets["google"]["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        r = requests.post(token_url, data=payload, timeout=10)
        new_tokens = r.json()
        
        if "access_token" not in new_tokens: 
            return None
        
        supabase.table("calendar_connections").update({
            "access_token": new_tokens["access_token"],
            "expires_in": new_tokens.get("expires_in", 3599)
        }).eq("user_id", user_id).eq("provider", "google").execute()
        
        return new_tokens["access_token"]
    except Exception as e:
        return None

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
        
        try:
            r = requests.get(url, headers=headers, timeout=5)
            
            if r.status_code == 401:
                new_token = refresh_google_token(user_id)
                if new_token:
                    headers = {"Authorization": f"Bearer {new_token}"}
                    r = requests.get(url, headers=headers, timeout=5)
                else: return []

            if r.status_code != 200:
                return []
        except requests.exceptions.Timeout:
            return []
        except Exception:
            return []
        
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

def book_google_meeting(user_id, subject, start_dt_utc, duration_minutes, attendees):
    if not supabase: return False, None
    try:
        token = get_provider_token(user_id, "google")
        if not token: 
            st.toast("❌ Google Calendar connection missing. Please reconnect in Settings.")
            return False, None

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        end_dt_utc = start_dt_utc + dt.timedelta(minutes=duration_minutes)
        
        attendee_list = [{"email": email.strip()} for email in attendees if is_valid_email(email)]

        start_str = start_dt_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        end_str = end_dt_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

        payload = {
            "summary": subject,
            "start": {"dateTime": start_str},
            "end": {"dateTime": end_str},
            "attendees": attendee_list,
            "conferenceData": {
                "createRequest": {
                    "requestId": f"nync_{user_id}_{int(dt.datetime.now().timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        }

        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events?sendUpdates=all&conferenceDataVersion=1"
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if r.status_code == 401:
            token = refresh_google_token(user_id)
            if not token:
                st.toast("❌ Google Calendar token completely expired. Disconnect & Reconnect in Settings.")
                return False, None
            headers["Authorization"] = f"Bearer {token}"
            r = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if r.status_code in [200, 201]:
            return True, r.json().get("hangoutLink")
        else:
            error_msg = r.json().get('error', {}).get('message', 'Unknown API Error')
            st.toast(f"Google API Error {r.status_code}: {error_msg}")
            return False, None
    except Exception as e: 
        print(f"Error booking Google Meeting: {e}")
        return False, None