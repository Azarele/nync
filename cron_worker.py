import os
import time
import datetime
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

import calendar_utils


def refresh_all_tokens():
    try:
        rows = supabase.table("calendar_connections").select("user_id, provider").execute()
        for row in rows.data:
            user_id = row.get("user_id")
            provider = row.get("provider", "")
            try:
                if provider == "google":
                    calendar_utils.refresh_google_token(user_id)
                elif provider == "outlook":
                    calendar_utils.refresh_outlook_token(user_id)
            except Exception as e:
                print(f"Failed to refresh token for user {user_id}: {e}")
    except Exception as e:
        print(f"refresh_all_tokens error: {e}")


def close_expired_polls():
    try:
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
        supabase.table("polls").update({"status": "closed"}).eq("status", "active").lt("created_at", cutoff).execute()
    except Exception as e:
        print(f"close_expired_polls error: {e}")

