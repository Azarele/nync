import pytz
from datetime import datetime, timedelta

# --- CONSTANTS ---
PAIN_MULTIPLIERS = {"ideal": 0, "annoying": 2, "painful": 3, "toxic": 10, "conflict": 100}

# --- 1. MATH ENGINE ---

def calculate_pain_score(local_h, is_blocked=False):
    if is_blocked: return PAIN_MULTIPLIERS["conflict"]
    if 9 <= local_h < 17: return PAIN_MULTIPLIERS["ideal"]
    if (7 <= local_h < 9) or (17 <= local_h < 19): return PAIN_MULTIPLIERS["annoying"]
    if (5 <= local_h < 7) or (19 <= local_h < 22): return PAIN_MULTIPLIERS["painful"]
    return PAIN_MULTIPLIERS["toxic"]

def perform_analysis(roster, busy_map, target_date_utc_start, history_map={}):
    """
    Finds the fairest slot considering HISTORICAL pain (Karma).
    history_map: { 'dave@email.com': 50, 'sarah@email.com': 0 }
    """
    scenarios = []
    
    for utc_hour in range(24):
        current_dt_utc = target_date_utc_start + timedelta(hours=utc_hour)
        breakdown = {} 
        
        meeting_total_pain = 0
        new_lifetime_balances = [] # Used to calculate fairness
        
        for member in roster:
            email = member['email']
            tz_name = member['tz']
            
            # 1. Calc Time
            try:
                tz_obj = pytz.timezone(tz_name)
                local_dt = current_dt_utc.astimezone(tz_obj)
                local_h = local_dt.hour
            except: local_h = utc_hour
            
            # 2. Check Blocked
            is_blocked = False
            if email in busy_map:
                if current_dt_utc in busy_map[email]: is_blocked = True
            
            # 3. Calc Meeting Pain
            p = calculate_pain_score(local_h, is_blocked)
            
            meeting_total_pain += p
            
            # 4. KARMA CALCULATION
            # Start with history, add this potential meeting
            current_balance = history_map.get(email, 0)
            projected_balance = current_balance + p
            new_lifetime_balances.append(projected_balance)

            breakdown[email] = {"name": member.get('name', email), "local_h": local_h, "pain": p, "blocked": is_blocked}
            
        # 5. The "Fairness Metric"
        # We want the slot that makes the difference between the most pained person 
        # and the least pained person as SMALL as possible.
        lifetime_gap = max(new_lifetime_balances) - min(new_lifetime_balances) if new_lifetime_balances else 0
        
        scenarios.append({
            "utc_hour": utc_hour,
            "total_pain": meeting_total_pain, # Still tracking this for reference
            "gap": lifetime_gap, # We optimize for THIS now
            "breakdown": breakdown
        })
        
    # Sort by: 
    # 1. Lowest Conflicts (Huge pain scores)
    # 2. Lowest Lifetime Gap (Fairness)
    # 3. Lowest Immediate Pain (Efficiency)
    scenarios.sort(key=lambda x: (x['total_pain'] >= 100, x['gap'], x['total_pain']))
    
    return scenarios[:3] if scenarios else []

# --- 2. DB RECORDING ---
def commit_booking(supabase, team_id, breakdown_dict, meeting_date):
    rows = []
    ts = meeting_date.isoformat() if hasattr(meeting_date, 'isoformat') else str(meeting_date)
    for email, data in breakdown_dict.items():
        rows.append({
            "team_id": team_id, "user_email": email, "pain_score": data['pain'], "meeting_date": ts
        })
    if rows:
        try:
            supabase.table('pain_ledger').insert(rows).execute()
            return True
        except: return False
    return False