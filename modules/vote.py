import streamlit as st
import pandas as pd
from datetime import datetime

def show(poll_id, supabase):
    # --- 1. SECURITY CHECK ---
    # User must be logged in to vote
    if 'user' not in st.session_state or not st.session_state.user:
        st.warning("🔒 You must be logged in to vote.")
        st.info("Please refresh the page or go to the dashboard to sign in.")
        if st.button("Go to Login"):
            st.query_params.clear()
            st.rerun()
        return

    # User is authenticated
    user_email = st.session_state.user.email
    st.title("🗳️ Cast Your Vote")
    
    # --- 2. FETCH POLL DATA ---
    try:
        poll = supabase.table('polls').select('*').eq('id', poll_id).single().execute()
        if not poll.data:
            st.error("Poll not found.")
            return

        options = supabase.table('poll_options').select('*').eq('poll_id', poll_id).order('pain_score').execute()
        if not options.data:
            st.error("No options found.")
            return
            
    except Exception as e:
        st.error("Error loading poll.")
        return

    # --- 3. DUPLICATE VOTE CHECK ---
    # Check if this user has already voted in this specific poll
    # We query strictly by their verified email
    existing_vote = supabase.table('poll_votes').select('*').eq('poll_id', poll_id).eq('voter_name', user_email).execute()
    
    if existing_vote.data:
        st.info(f"✅ You have already voted, {user_email.split('@')[0]}!")
        show_results(supabase, poll_id, options.data)
        return

    # --- 4. CHECK FOR PRE-SELECTION ---
    pre_selected_index = 0
    if "idx" in st.query_params:
        try:
            val = int(st.query_params["idx"])
            if 0 <= val < len(options.data):
                pre_selected_index = val
        except: pass

    # --- 5. VOTING FORM (Restricted) ---
    st.write(f"Voting as: **{user_email}**") # Show them who they are
    
    with st.form("voting_form"):
        # We REMOVED the name input field. Identity is now hardcoded.
        
        radio_keys = []
        radio_ids = []
        for opt in options.data:
            dt = datetime.fromisoformat(opt['slot_time'].replace('Z', '+00:00'))
            label = f"{dt.strftime('%H:%M')} UTC  (Team Pain: {opt['pain_score']})"
            radio_keys.append(label)
            radio_ids.append(opt['id'])
            
        selected_label = st.radio("Select a Time:", radio_keys, index=pre_selected_index)
        
        sel_idx = radio_keys.index(selected_label)
        selected_id = radio_ids[sel_idx]
        
        if st.form_submit_button("Submit Vote", type="primary", width="stretch"):
            try:
                supabase.table('poll_votes').insert({
                    'poll_id': poll_id,
                    'option_id': selected_id,
                    'voter_name': user_email # FORCED: Uses authenticated email
                }).execute()
                st.toast("✅ Vote Recorded!")
                st.rerun() # Rerun to trigger the "Already Voted" view
            except Exception as e:
                st.error(f"Failed to save vote: {e}")

    st.divider()
    # Optional: Show current results below form if you want them to see it before voting
    # For now, we only show it after voting (in the 'Already Voted' block) or if we duplicate logic.
    # Let's show a preview of total counts anyway for transparency:
    st.caption("Live Vote Counts")
    show_results(supabase, poll_id, options.data, simple=True)

def show_results(supabase, poll_id, options_data, simple=False):
    """Helper to display the bar chart or list of results"""
    if not simple: st.subheader("📊 Live Results")
    
    votes = supabase.table('poll_votes').select('option_id').eq('poll_id', poll_id).execute()
    
    if votes.data:
        tally = {}
        for v in votes.data:
            oid = v['option_id']
            tally[oid] = tally.get(oid, 0) + 1
            
        for opt in options_data:
            dt = datetime.fromisoformat(opt['slot_time'].replace('Z', '+00:00'))
            label = dt.strftime('%H:%M UTC')
            count = tally.get(opt['id'], 0)
            
            # Simple bar visualization
            bar = "🟦" * count
            st.write(f"**{label}**: {count} {bar}")
    else:
        st.info("No votes yet.")