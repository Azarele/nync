import streamlit as st
import datetime as dt
from db import supabase

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
def check_calendar_connected(user_id):
    if not supabase: return False
    try:
        res = supabase.table("calendar_connections").select("id").eq("user_id", user_id).limit(1).execute()
        return len(res.data) > 0
    except: return False

@st.cache_data(ttl=300)
def get_team_roster(team_id):
    if not supabase: return []
    try:
        # Added work_start_hour and work_end_hour to the fetch list!
        res = supabase.table('team_members').select('id, user_id, role, ghost_name, ghost_email, ghost_timezone, profiles(email, default_timezone, work_start_hour, work_end_hour)').eq('team_id', team_id).execute()
        
        roster = []
        for m in res.data:
            if m.get('user_id'): 
                prof = m.get('profiles') or {}
                # Safely pull the work hours, defaulting to 9 and 17 if not set yet
                w_start = prof.get('work_start_hour') if prof.get('work_start_hour') is not None else 9
                w_end = prof.get('work_end_hour') if prof.get('work_end_hour') is not None else 17
                
                roster.append({
                    'id': m['id'], 'user_id': m['user_id'], 'role': m.get('role', 'member'),
                    'email': prof.get('email', 'Unknown'), 'name': prof.get('email', 'Unknown').split('@')[0], 
                    'tz': prof.get('default_timezone') or 'UTC',
                    'work_start': w_start, 'work_end': w_end
                })
            else:
                roster.append({
                    'id': m['id'], 'user_id': None, 'role': 'ghost',
                    'email': m.get('ghost_email') or '', 'name': m.get('ghost_name') or 'Ghost', 
                    'tz': m.get('ghost_timezone') or 'UTC',
                    'work_start': 9, 'work_end': 17 # Ghosts default to 9-to-5
                })
        return roster
    except Exception as e: 
        import streamlit as st
        st.error(f"🚨 DATABASE ERROR: {e}") # This will print the exact issue on your dashboard!
        return []

def check_team_status(team_id):
    try:
        team = supabase.table('teams').select('trial_ends_at, created_by').eq('id', team_id).single().execute()
        if not team.data: return 'active'
        
        creator_id = team.data.get('created_by')
        tier = 'free'
        if creator_id:
            prof = supabase.table('profiles').select('subscription_tier').eq('id', creator_id).maybe_single().execute()
            if prof and prof.data:
                tier = prof.data.get('subscription_tier', 'free').lower()
                
        if tier in ['squad', 'guild', 'empire']: return 'active'

        trial_end_str = team.data.get('trial_ends_at')
        if not trial_end_str: return 'active'
        trial_end = dt.datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
        is_expired = dt.datetime.now(trial_end.tzinfo) > trial_end
        
        count = supabase.table('team_members').select('*', count='exact').eq('team_id', team_id).execute().count
        if is_expired and count > 3: return 'locked'
        
        return 'active'
    except Exception as e: 
        print(f"Status check error: {e}")
        return 'active'

def remove_team_member(team_id, member_id_to_remove, current_user_id):
    if not supabase: return False
    try:
        admin_check = supabase.table('team_members').select('role').eq('team_id', team_id).eq('user_id', current_user_id).execute()
        if not admin_check.data or admin_check.data[0].get('role') != 'admin':
            st.error("Only Admins can remove members.")
            return False

        if member_id_to_remove == current_user_id:
            admin_count = supabase.table('team_members').select('*', count='exact').eq('team_id', team_id).eq('role', 'admin').execute().count
            if admin_count <= 1:
                st.error("You cannot leave the team because you are the only Admin. Assign another Admin first or delete the team.")
                return False

        supabase.table('team_members').delete().eq('team_id', team_id).eq('user_id', member_id_to_remove).execute()
        get_team_roster.clear()
        get_user_teams.clear()
        return True
    except Exception as e:
        st.error(f"Failed to remove member: {e}")
        return False

def remove_team_member_by_row(row_id, team_id, current_user_id):
    if not supabase: return False
    try:
        admin_check = supabase.table('team_members').select('role').eq('team_id', team_id).eq('user_id', current_user_id).execute()
        if not admin_check.data or admin_check.data[0].get('role') != 'admin':
            st.error("Only Admins can remove members.")
            return False

        target = supabase.table('team_members').select('user_id').eq('id', row_id).execute()
        if target.data and target.data[0].get('user_id') == current_user_id:
            admin_count = supabase.table('team_members').select('*', count='exact').eq('team_id', team_id).eq('role', 'admin').execute().count
            if admin_count <= 1:
                st.error("Cannot remove yourself. You are the only admin.")
                return False

        supabase.table('team_members').delete().eq('id', row_id).execute()
        get_team_roster.clear()
        get_user_teams.clear()
        return True
    except Exception as e:
        print(f"Error removing member: {e}")
        return False

def leave_team(team_id, current_user_id):
    if not supabase: return False
    try:
        admin_count = supabase.table('team_members').select('*', count='exact').eq('team_id', team_id).eq('role', 'admin').execute().count
        my_role = supabase.table('team_members').select('role').eq('team_id', team_id).eq('user_id', current_user_id).execute()
        if my_role.data and my_role.data[0].get('role') == 'admin' and admin_count <= 1:
            st.error("You cannot leave as the only Admin. Delete the team or promote someone else.")
            return False
            
        supabase.table('team_members').delete().eq('team_id', team_id).eq('user_id', current_user_id).execute()
        get_user_teams.clear()
        get_team_roster.clear()
        return True
    except Exception as e:
        print(e)
        return False

def add_ghost_member(team_id, name, email, timezone, current_user_id):
    if not supabase: return False
    try:
        admin_check = supabase.table('team_members').select('role').eq('team_id', team_id).eq('user_id', current_user_id).execute()
        if not admin_check.data or admin_check.data[0].get('role') != 'admin':
            return False
            
        supabase.table('team_members').insert({
            'team_id': team_id,
            'ghost_name': name,
            'ghost_email': email,
            'ghost_timezone': timezone,
            'role': 'member'
        }).execute()
        
        get_team_roster.clear()
        return True
    except Exception as e:
        print(f"Error adding ghost: {e}")
        return False

def update_member_timezone(row_id, user_id, new_timezone, is_ghost):
    if not supabase: return False
    try:
        if is_ghost:
            supabase.table('team_members').update({'ghost_timezone': new_timezone}).eq('id', row_id).execute()
        else:
            res = supabase.table('profiles').update({'default_timezone': new_timezone}).eq('id', user_id).execute()
            if not res.data: pass 
            
        get_team_roster.clear()
        return True
    except Exception as e:
        print(f"Error updating tz: {e}")
        return False

def join_team_by_code(user_id, code):
    try:
        clean_code = str(code).strip().upper()
        t = supabase.table('teams').select('id, name').eq('invite_code', clean_code).execute()
        if not t.data: return False
            
        tid, name = t.data[0]['id'], t.data[0]['name']
        existing = supabase.table('team_members').select('*').eq('team_id', tid).eq('user_id', user_id).execute()
        if existing.data: return True
            
        supabase.table('team_members').insert({'team_id': tid, 'user_id': user_id, 'role': 'member'}).execute()
        st.session_state.active_team = name
        get_user_teams.clear() 
        return True
    except Exception as e: 
        print(f"Error joining team: {e}") 
        return False

def create_team(user_id, name):
    import secrets, string
    code = "NYNC-" + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    try:
        t = supabase.table('teams').insert({'name': name, 'invite_code': code, 'created_by': user_id}).execute()
        if not t.data: 
            st.error("Database returned no data. Check Row Level Security (RLS) policies.")
            return False
        tid = t.data[0]['id']
        supabase.table('team_members').insert({'team_id': tid, 'user_id': user_id, 'role': 'admin'}).execute()
        st.session_state.active_team = name
        try: get_user_teams.clear()
        except: pass 
        return True
    except Exception as e: 
        st.error(f"Database Error: {e}")
        return False