from datetime import datetime, timedelta

def generate_ics_file(utc_hour, roster, title, date_obj):
    """
    Creates a standard .ics calendar file content.
    """
    # 1. Calculate Start/End Times in UTC
    # Format required by ICS: YYYYMMDDTHHMMSSZ
    start_dt = datetime.combine(date_obj, datetime.min.time()) + timedelta(hours=utc_hour)
    end_dt = start_dt + timedelta(hours=1) # Default 1 hour meeting
    
    dt_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dt_start = start_dt.strftime("%Y%m%dT%H%M%SZ")
    dt_end = end_dt.strftime("%Y%m%dT%H%M%SZ")
    
    # 2. Build Description (Who is suffering?)
    description = "Pain Report:\\n"
    for m in roster:
        # Handle cases where name might be missing
        name = m.get('name') or m.get('email', 'Unknown').split('@')[0]
        tz = m.get('tz', 'UTC')
        description += f"- {name} ({tz})\\n"
    
    # 3. Build the file content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Nync//Martyr Scheduler//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{dt_stamp}-nync@scheduler
DTSTAMP:{dt_stamp}
DTSTART:{dt_start}
DTEND:{dt_end}
SUMMARY:⚡ {title} (Nync)
DESCRIPTION:{description}
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT
END:VCALENDAR"""
    
    return ics_content