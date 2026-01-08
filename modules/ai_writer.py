import openai
import streamlit as st

def draft_diplomatic_invite(slot_time, participants):
    """
    Uses AI to write a meeting invite using REAL NAMES.
    Expects participants to be a list of dicts: [{'name': 'Sarah', 'score': 0}, ...]
    """
    # 1. Check for API Key
    if "openai" not in st.secrets:
        return "⚠️ AI Error: Please add your OpenAI API Key to secrets.toml"
    
    client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])

    # 2. Analyze the Pain Data
    context_str = f"Meeting Time: {slot_time}\nParticipants:\n"
    
    if not participants:
        return "Error: No participant data found."

    # Find the maximum pain score
    max_pain = max(p['score'] for p in participants)

    # Find ALL martyrs (handling ties) using their NAMES
    martyrs = [p['name'] for p in participants if p['score'] == max_pain]
    
    # Add everyone to the context string
    for p in participants:
        context_str += f"- {p['name']}: Pain Score {p['score']}/100\n"

    # 3. Dynamic Prompting
    tone_instruction = ""
    
    if max_pain < 5:
        tone_instruction = "Everyone has low pain. Celebrate that we found a 'Unicorn' slot where nobody suffers. It's a miracle."
    elif len(martyrs) > 1:
        names = ", ".join(martyrs)
        tone_instruction = f"There is a TIE for the highest pain ({max_pain}). The martyrs are: {names}. Acknowledge that they are ALL sharing the burden equally. Do not single out just one."
    else:
        martyr_name = martyrs[0]
        tone_instruction = f"One person ({martyr_name}) has the highest pain ({max_pain}). Explicitly thank them for taking one for the team."

    prompt = f"""
    You are an empathetic and witty assistant for 'Nync', a fair scheduling tool.
    Write a short calendar invite description (under 50 words).

    SCENARIO DATA:
    {context_str}

    INSTRUCTIONS:
    1. Start by confirming the meeting time.
    2. {tone_instruction}
    3. Use the participants' names naturally.
    4. Keep it fun, professional, and acknowledging of time zone struggles.
    """

    # 4. Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating message: {e}"