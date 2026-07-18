import datetime
from db import supabase
import calendar_utils


def refresh_all_tokens():
    """Only refresh tokens expiring within the next 30 minutes."""
    if not supabase:
        return
    try:
        cutoff = (datetime.datetime.utcnow() + datetime.timedelta(minutes=30)).isoformat()
        rows = supabase.table("calendar_connections") \
            .select("user_id, provider") \
            .lt("expires_at", cutoff) \
            .execute()

        if not rows.data:
            return

        for row in rows.data:
            user_id = row.get("user_id")
            provider = row.get("provider", "")
            try:
                if provider == "google":
                    calendar_utils.refresh_google_token(user_id)
                elif provider == "outlook":
                    calendar_utils.refresh_outlook_token(user_id)
            except Exception as e:
                print(f"[nync] Failed to refresh {provider} token for user {user_id}: {e}")

    except Exception as e:
        print(f"[nync] refresh_all_tokens error: {e}")


def close_expired_polls():
    """Close polls that have been active for more than 7 days."""
    if not supabase:
        return
    try:
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
        supabase.table("polls") \
            .update({"status": "closed"}) \
            .eq("status", "active") \
            .lt("created_at", cutoff) \
            .execute()
    except Exception as e:
        print(f"[nync] close_expired_polls error: {e}")
