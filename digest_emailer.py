import os
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Leads"
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASS = os.getenv("SMTP_PASSWORD")
RECIPIENT = os.getenv("RECIPIENT_EMAIL")

def get_recent_leads():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    formula = f"AND(IS_AFTER({{Created At}}, '{yesterday}'), Score >= 7)"
    params = {"filterByFormula": formula}
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json().get("records", [])

def send_digest_email(leads):
    if not leads:
        return
    msg = EmailMessage()
    msg["Subject"] = f"📬 Daily Digest: {len(leads)} Leads"
    msg["From"] = SMTP_EMAIL
    msg["To"] = RECIPIENT

    body_plain = ""
    rows = []
    for lead in leads:
        f = lead["fields"]
        body_plain += f"Name: {f.get('Name')}, Score: {f.get('Score')}, {f.get('Category')}, {f.get('LinkedIn URL')}\n"
        rows.append(f)

    msg.set_content(body_plain)

    df = pd.DataFrame(rows)
    csv_data = StringIO()
    df.to_csv(csv_data, index=False)
    msg.add_attachment(csv_data.getvalue().encode(), maintype='text', subtype='csv', filename='leads.csv')

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_EMAIL, SMTP_PASS)
        smtp.send_message(msg)