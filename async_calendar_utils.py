import asyncio
import aiohttp
import datetime as dt
from db import supabase
import streamlit as st

async def fetch_outlook_events_async(session, user_id, start_dt, end_dt):
    """Asynchronously fetches Microsoft Graph events for a single user."""
    try:
        # We still use the synchronous DB call here to get the token quickly
        response = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", "outlook").maybe_single().execute()
        if not response or not response.data: return user_id, []
        token = response.data.get('access_token')

        headers = {"Authorization": f"Bearer {token}", "Prefer": "outlook.timezone=\"UTC\""}
        start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        endpoint = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={start_str}&endDateTime={end_str}&$select=subject,start,end,showAs"
        
        async with session.get(endpoint, headers=headers, timeout=5) as r:
            if r.status != 200: return user_id, []
            data = await r.json()
            
            events = data.get('value', [])
            blocked_strs = set()
            for e in events:
                start = dt.datetime.fromisoformat(e['start']['dateTime'].replace('Z', '+00:00'))
                end = dt.datetime.fromisoformat(e['end']['dateTime'].replace('Z', '+00:00'))
                
                # Force to naive UTC for safe matching in the Pain Engine
                start_naive = start.astimezone(dt.timezone.utc).replace(tzinfo=None)
                end_naive = end.astimezone(dt.timezone.utc).replace(tzinfo=None)
                
                curr = start_naive
                while curr < end_naive:
                    blocked_strs.add(curr.replace(minute=0, second=0, microsecond=0).isoformat())
                    curr += dt.timedelta(hours=1)
                    
            return user_id, list(blocked_strs)
    except:
        return user_id, []

async def fetch_google_events_async(session, user_id, start_dt, end_dt):
    """Asynchronously fetches Google Calendar events for a single user."""
    try:
        response = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", "google").maybe_single().execute()
        if not response or not response.data: return user_id, []
        token = response.data.get('access_token')

        start_str = start_dt.isoformat() + "Z"
        end_str = end_dt.isoformat() + "Z"
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={start_str}&timeMax={end_str}&singleEvents=true"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(url, headers=headers, timeout=5) as r:
            if r.status != 200: return user_id, []
            data = await r.json()
            
            items = data.get('items', [])
            blocked_strs = set()
            for i in items:
                if 'dateTime' not in i.get('start', {}): continue
                
                start = dt.datetime.fromisoformat(i['start']['dateTime'])
                end = dt.datetime.fromisoformat(i['end']['dateTime'])
                
                start_naive = start.astimezone(dt.timezone.utc).replace(tzinfo=None) if start.tzinfo else start
                end_naive = end.astimezone(dt.timezone.utc).replace(tzinfo=None) if end.tzinfo else end
                
                curr = start_naive
                while curr < end_naive:
                    blocked_strs.add(curr.replace(minute=0, second=0, microsecond=0).isoformat())
                    curr += dt.timedelta(hours=1)
                    
            return user_id, list(blocked_strs)
    except:
        return user_id, []

async def gather_all_conflicts(roster, start_date, days):
    """The master Async function that fires all requests in parallel."""
    start_dt = dt.datetime.combine(start_date, dt.time.min) 
    end_dt = start_dt + dt.timedelta(days=days)
    
    # Pre-fetch the connections for the whole team in one single synchronous DB call to save time!
    user_ids = [m.get('user_id') for m in roster if m.get('user_id')]
    if not user_ids: return {}
    
    res = supabase.table('calendar_connections').select('user_id, provider').in_('user_id', user_ids).execute()
    connections = res.data if res.data else []
    
    tasks = []
    
    # We open ONE connection session to handle all the outbound requests
    async with aiohttp.ClientSession() as session:
        for conn in connections:
            uid = conn['user_id']
            provider = conn['provider']
            
            # Fire the requests into the event loop!
            if provider == 'outlook':
                tasks.append(fetch_outlook_events_async(session, uid, start_dt, end_dt))
            elif provider == 'google':
                tasks.append(fetch_google_events_async(session, uid, start_dt, end_dt))
                
        # Gather all the results at the exact same time
        results = await asyncio.gather(*tasks)
        
    # Rebuild the dictionary for the Pain Engine
    conflicts_dict = {}
    for uid, blocks in results:
        if str(uid) not in conflicts_dict:
            conflicts_dict[str(uid)] = set(blocks)
        else:
            conflicts_dict[str(uid)].update(blocks)
            
    # Convert sets back to lists for JSON serialization
    return {k: list(v) for k, v in conflicts_dict.items()}