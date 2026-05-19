import asyncio
import aiohttp
import datetime as dt
from db import supabase
import streamlit as st

async def fetch_outlook_events_async(session, user_id, start_dt, end_dt):
    try:
        response = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", "outlook").maybe_single().execute()
        if not response or not response.data: return user_id, {}
        token = response.data.get('access_token')

        headers = {"Authorization": f"Bearer {token}", "Prefer": "outlook.timezone=\"UTC\""}
        start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        endpoint = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={start_str}&endDateTime={end_str}&$select=subject,start,end,showAs"

        async with session.get(endpoint, headers=headers, timeout=5) as r:
            if r.status != 200: return user_id, {}
            data = await r.json()

            blocked = {}
            for e in data.get('value', []):
                title = e.get('subject', 'Busy')
                start = dt.datetime.fromisoformat(e['start']['dateTime'].replace('Z', '+00:00'))
                end = dt.datetime.fromisoformat(e['end']['dateTime'].replace('Z', '+00:00'))
                start_naive = start.astimezone(dt.timezone.utc).replace(tzinfo=None)
                end_naive = end.astimezone(dt.timezone.utc).replace(tzinfo=None)
                curr = start_naive
                while curr < end_naive:
                    blocked[curr.replace(minute=0, second=0, microsecond=0).isoformat()] = title
                    curr += dt.timedelta(hours=1)

            return user_id, blocked
    except:
        return user_id, {}

async def fetch_google_events_async(session, user_id, start_dt, end_dt):
    try:
        response = supabase.table("calendar_connections").select("access_token").eq("user_id", user_id).eq("provider", "google").maybe_single().execute()
        if not response or not response.data: return user_id, {}
        token = response.data.get('access_token')

        start_str = start_dt.isoformat() + "Z"
        end_str = end_dt.isoformat() + "Z"
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={start_str}&timeMax={end_str}&singleEvents=true"
        headers = {"Authorization": f"Bearer {token}"}

        async with session.get(url, headers=headers, timeout=5) as r:
            if r.status != 200: return user_id, {}
            data = await r.json()

            blocked = {}
            for i in data.get('items', []):
                if 'dateTime' not in i.get('start', {}): continue
                title = i.get('summary', 'Busy')
                start = dt.datetime.fromisoformat(i['start']['dateTime'])
                end = dt.datetime.fromisoformat(i['end']['dateTime'])
                start_naive = start.astimezone(dt.timezone.utc).replace(tzinfo=None) if start.tzinfo else start
                end_naive = end.astimezone(dt.timezone.utc).replace(tzinfo=None) if end.tzinfo else end
                curr = start_naive
                while curr < end_naive:
                    blocked[curr.replace(minute=0, second=0, microsecond=0).isoformat()] = title
                    curr += dt.timedelta(hours=1)

            return user_id, blocked
    except:
        return user_id, {}

async def gather_all_conflicts(roster, start_date, days):
    start_dt = dt.datetime.combine(start_date, dt.time.min)
    end_dt = start_dt + dt.timedelta(days=days)

    user_ids = [m.get('user_id') for m in roster if m.get('user_id')]
    if not user_ids: return {}

    res = supabase.table('calendar_connections').select('user_id, provider').in_('user_id', user_ids).execute()
    connections = res.data if res.data else []

    tasks = []
    async with aiohttp.ClientSession() as session:
        for conn in connections:
            uid = conn['user_id']
            provider = conn['provider']
            if provider == 'outlook':
                tasks.append(fetch_outlook_events_async(session, uid, start_dt, end_dt))
            elif provider == 'google':
                tasks.append(fetch_google_events_async(session, uid, start_dt, end_dt))
        results = await asyncio.gather(*tasks)

    conflicts_dict = {}
    for uid, blocks in results:
        if str(uid) not in conflicts_dict:
            conflicts_dict[str(uid)] = blocks
        else:
            conflicts_dict[str(uid)].update(blocks)

    return conflicts_dict
