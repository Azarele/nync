import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_poll_email(recipient_emails, team_name, target_date, chosen_time):
    """Blasts a beautifully formatted HTML email to the roster."""
    try:
        # We use Streamlit Secrets to safely store email credentials
        if "smtp" not in st.secrets:
            print("No SMTP credentials found in secrets.")
            return False
            
        smtp_server = st.secrets["smtp"]["server"]
        smtp_port = st.secrets["smtp"]["port"]
        sender_email = st.secrets["smtp"]["email"]
        sender_password = st.secrets["smtp"]["password"]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🗳️ New Meeting Proposed: {team_name}"
        msg["From"] = f"Nync App <{sender_email}>"

        # Beautiful Branded HTML Template
        html_content = f"""
        <html>
        <body style="font-family: 'Inter', Arial, sans-serif; background-color: #f4f4f5; padding: 40px 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                <h2 style="color: #111827; margin-bottom: 5px;">New Meeting Proposed</h2>
                <p style="color: #6b7280; font-size: 16px; line-height: 1.5;">A new sync time has been proposed for <strong>{team_name}</strong>.</p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-left: 4px solid #4f46e5; border-radius: 4px; margin: 30px 0;">
                    <p style="margin: 0 0 10px 0; font-size: 16px;">🗓️ <strong>Date:</strong> {target_date.strftime('%A, %B %d, %Y')}</p>
                    <p style="margin: 0; font-size: 16px;">⏰ <strong>Time:</strong> {chosen_time}</p>
                </div>
                
                <p style="color: #4b5563; font-size: 15px; line-height: 1.5; margin-bottom: 30px;">
                    Please click the button below to visit the Pain Board and cast your vote on whether this time works for you.
                </p>
                
                <a href="https://nync.app" style="display: inline-block; background-color: #4f46e5; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">🗳️ Vote on Pain Board</a>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin-top: 40px; margin-bottom: 20px;">
                <p style="font-size: 12px; color: #9ca3af; text-align: center;">Sent securely by Nync Scheduler.</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            # Send using envelope Bcc to hide emails from each other
            server.sendmail(sender_email, recipient_emails, msg.as_string())
        return True
        
    except Exception as e:
        print(f"Failed to send email blast: {e}")
        return False

def send_booking_email(recipient_emails, team_name, target_date, chosen_time, video_link):
    """Blasts the final confirmation and video link when a meeting is locked."""
    try:
        if "smtp" not in st.secrets: return False
            
        smtp_server = st.secrets["smtp"]["server"]
        smtp_port = st.secrets["smtp"]["port"]
        sender_email = st.secrets["smtp"]["email"]
        sender_password = st.secrets["smtp"]["password"]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"✅ Meeting Locked: {team_name}"
        msg["From"] = f"Nync App <{sender_email}>"

        # Build dynamic video button
        video_html = f"""
        <div style="margin-top: 30px; text-align: center;">
            <a href="{video_link}" style="display: inline-block; background-color: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">🎥 Join Video Call</a>
        </div>
        """ if video_link else ""

        html_content = f"""
        <html>
        <body style="font-family: 'Inter', Arial, sans-serif; background-color: #f4f4f5; padding: 40px 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
                <h2 style="color: #111827; margin-bottom: 5px;">Meeting Locked!</h2>
                <p style="color: #6b7280; font-size: 16px; line-height: 1.5;">The poll has finished and the final meeting time for <strong>{team_name}</strong> is locked in.</p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-left: 4px solid #10b981; border-radius: 4px; margin: 30px 0;">
                    <p style="margin: 0 0 10px 0; font-size: 16px;">🗓️ <strong>Date:</strong> {target_date.strftime('%A, %B %d, %Y')}</p>
                    <p style="margin: 0; font-size: 16px;">⏰ <strong>Time:</strong> {chosen_time}</p>
                </div>
                
                {video_html}
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin-top: 40px; margin-bottom: 20px;">
                <p style="font-size: 12px; color: #9ca3af; text-align: center;">Sent securely by Nync Scheduler.</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())
        return True
        
    except Exception as e:
        print(f"Failed to send booking email blast: {e}")
        return False